#!/usr/bin/env python
# Copyright 2015-2016 Yelp Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import argparse
import json
import time
from random import choice

import pysensu_yelp
from scribereader import scribereader

from paasta_tools import monitoring_tools
from paasta_tools.chronos_tools import compose_check_name_for_service_instance
from paasta_tools.cli.utils import get_instance_config
from paasta_tools.utils import DEFAULT_SOA_DIR
from paasta_tools.utils import get_services_for_cluster
from paasta_tools.utils import load_system_paasta_config


def parse_args():
    parser = argparse.ArgumentParser(description=(
        'Check the tmp_paasta_oom_events stream and report to Sensu '
        'if there are any OOM events.',
    ))
    parser.add_argument(
        '-d', '--soa-dir', dest="soa_dir", metavar="SOA_DIR",
        default=DEFAULT_SOA_DIR,
        help="define a different soa config directory",
    )
    parser.add_argument(
        '-s', '--superregion', dest="superregion", required=True,
        help="The superregion to use",
    )
    return parser.parse_args()


def oom_events(cluster, superregion, num_lines=1000):
    """Iterate over latest 'num_lines' lines in the tmp_paasta_oom_events stream"""
    host_and_port = choice(scribereader.get_default_scribe_hosts(tail=True))
    host = host_and_port['host']
    port = host_and_port['port']
    stream = scribereader.get_stream_tailer(
        'tmp_paasta_oom_events', host, port, True,
        num_lines, superregion=superregion,
    )
    for line in stream:
        try:
            j = json.loads(line)
            if j.get('cluster', '') == cluster:
                yield j
        except json.decoder.JSONDecodeError:
            pass


def latest_oom_events(cluster, superregion, interval=60):
    """
    :returns: {(service, instance): [(hostname, container_id, process_name), ...] }
              if the number of events > 0
    """
    start_timestamp = int(time.time()) - interval
    res = {}
    for e in oom_events(cluster, superregion):
        if e['timestamp'] > start_timestamp:
            key = (e['service'], e['instance'])
            res.setdefault(key, []).append((
                e.get('hostname', ''),
                e.get('container_id', ''),
                e.get('process_name', ''),
            ))
    return res


def compose_sensu_status(service_instance, events):
    """
    :param service_instance: a tuple (service, instance)
    :param events: a list of tuples (hostname, container_id, process_name)
    """
    if len(events) == 0:
        return (
            pysensu_yelp.Status.OK,
            'oom-killer is not killing processes in %s.%s containers.' %
            (service_instance[0], service_instance[1]),
        )
    else:
        return (
            pysensu_yelp.Status.CRITICAL,
            'oom-killer is killing %d processes a minute in %s.%s containers.' %
            (len(events), service_instance[0], service_instance[1]),
        )


def send_sensu_event(instance, status):
    check_name = compose_check_name_for_service_instance(
        'check_oom_events',
        instance.service,
        instance.instance,
    )
    monitoring_overrides = instance.get_monitoring()
    monitoring_overrides['page'] = False
    monitoring_overrides['ticket'] = False
    monitoring_overrides['team'] = 'noop'
    monitoring_overrides['irc_channels'] = ['#adudkotest']
    monitoring_overrides['runbook'] = ['http://y/none']
    monitoring_tools.send_event(
        service=instance.service,
        check_name=check_name,
        overrides=monitoring_overrides,
        status=status[0],
        output=status[1],
        soa_dir=instance.soa_dir,
    )


def main():
    args = parse_args()
    cluster = load_system_paasta_config().get_cluster()
    victims = latest_oom_events(cluster, args.superregion)
    for s_i in get_services_for_cluster(cluster):
        instance = get_instance_config(
            s_i[0], s_i[1], cluster,
            load_deployments=False, soa_dir=args.soa_dir,
        )
        send_sensu_event(instance, compose_sensu_status(s_i, victims.get(s_i, [])))


if __name__ == '__main__':
    main()
