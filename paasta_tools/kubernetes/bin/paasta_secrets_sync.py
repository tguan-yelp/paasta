#!/usr/bin/env python
# Copyright 2015-2019 Yelp Inc.
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
import hashlib
import json
import logging
import os
import sys
from typing import Mapping
from typing import Sequence

import yaml
from kubernetes.client.rest import ApiException

from paasta_tools.kubernetes_tools import create_kubernetes_secret_signature
from paasta_tools.kubernetes_tools import create_plaintext_dict_secret
from paasta_tools.kubernetes_tools import create_secret
from paasta_tools.kubernetes_tools import get_kubernetes_secret_signature
from paasta_tools.kubernetes_tools import KubeClient
from paasta_tools.kubernetes_tools import update_kubernetes_secret_signature
from paasta_tools.kubernetes_tools import update_plaintext_dict_secret
from paasta_tools.kubernetes_tools import update_secret
from paasta_tools.secret_tools import get_secret_provider
from paasta_tools.utils import DEFAULT_SOA_DIR
from paasta_tools.utils import load_system_paasta_config


log = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync paasta secrets into k8s")
    parser.add_argument(
        "service_list",
        nargs="+",
        help="The list of services to sync secrets for",
        metavar="SERVICE",
    )
    parser.add_argument(
        "-c",
        "--cluster",
        dest="cluster",
        metavar="CLUSTER",
        default=None,
        help="Kubernetes cluster name",
    )
    parser.add_argument(
        "-d",
        "--soa-dir",
        dest="soa_dir",
        metavar="SOA_DIR",
        default=DEFAULT_SOA_DIR,
        help="define a different soa config directory",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", dest="verbose", default=False
    )
    args = parser.parse_args()
    return args


def main() -> None:
    args = parse_args()
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)

    system_paasta_config = load_system_paasta_config()
    if args.cluster:
        cluster = args.cluster
    else:
        cluster = system_paasta_config.get_cluster()
    secret_provider_name = system_paasta_config.get_secret_provider_name()
    vault_cluster_config = system_paasta_config.get_vault_cluster_config()
    kube_client = KubeClient()
    sys.exit(0) if sync_all_secrets(
        kube_client=kube_client,
        cluster=cluster,
        service_list=args.service_list,
        secret_provider_name=secret_provider_name,
        vault_cluster_config=vault_cluster_config,
        soa_dir=args.soa_dir,
    ) else sys.exit(1)


def sync_all_secrets(
    kube_client: KubeClient,
    cluster: str,
    service_list: Sequence[str],
    secret_provider_name: str,
    vault_cluster_config: Mapping[str, str],
    soa_dir: str,
) -> bool:
    results = []
    for service in service_list:
        results.append(
            sync_secrets(
                kube_client=kube_client,
                cluster=cluster,
                service=service,
                secret_provider_name=secret_provider_name,
                vault_cluster_config=vault_cluster_config,
                soa_dir=soa_dir,
            )
        )
    return all(results)


def sync_secrets(
    kube_client: KubeClient,
    cluster: str,
    service: str,
    secret_provider_name: str,
    vault_cluster_config: Mapping[str, str],
    soa_dir: str,
) -> bool:
    secret_dir = os.path.join(soa_dir, service, "secrets")
    secret_provider_kwargs = {
        "vault_cluster_config": vault_cluster_config,
        # TODO: make vault-tools support k8s auth method so we don't have to
        # mount a token in.
        "vault_auth_method": "token",
        "vault_token_file": "/root/.vault_token",
    }
    secret_provider = get_secret_provider(
        secret_provider_name=secret_provider_name,
        soa_dir=soa_dir,
        service_name=service,
        cluster_names=[cluster],
        secret_provider_kwargs=secret_provider_kwargs,
    )
    if not os.path.isdir(secret_dir):
        log.debug(f"No secrets dir for {service}")
        return True

    # Update boto key secrets
    service_dir = os.path.join(soa_dir, service)
    kubernetes_config_file = f"kubernetes-{cluster}.yaml"
    full_config_path = os.path.join(service_dir, kubernetes_config_file)
    if os.path.exists(full_config_path):
        with open(full_config_path) as f:
            kubernetes_config = yaml.load(f.read())
        for instance, instance_config in kubernetes_config.items():
            if instance.startswith("_"):
                continue
            boto_keys = instance_config.get("boto_keys", [])
            if not boto_keys:
                continue
            boto_keys.sort()
            secret_data = {}
            for key in boto_keys:
                try:
                    with open(f"/etc/boto_cfg/{key}") as f:
                        secret_data[key] = f.read()
                except IOError:
                    pass
            if not secret_data:
                continue
            secret = f"paasta-boto-key-{service}-{instance}"
            hashable_data = "".join([secret_data.get(key, "") for key in boto_keys])
            signature = hashlib.sha1(hashable_data)
            kubernetes_signature = get_kubernetes_secret_signature(
                kube_client=kube_client, secret=secret, service=service
            )
            if not kubernetes_signature:
                log.info(f"{secret} for {service} not found, creating")
                try:
                    create_plaintext_dict_secret(
                        kube_client=kube_client,
                        secret_name=secret,
                        secret_data=secret_data,
                        service=service,
                    )
                except ApiException as e:
                    if e.status == 409:
                        log.warning(f"Secret {secret} for {service} already exists")
                    else:
                        raise
                create_kubernetes_secret_signature(
                    kube_client=kube_client,
                    secret=secret,
                    service=service,
                    secret_signature=signature,
                )
            elif signature != kubernetes_signature:
                log.info(f"{secret} for {service} needs updating as signature changed")
                update_plaintext_dict_secret(
                    kube_client=kube_client,
                    secret_name=secret,
                    secret_data=secret_data,
                    service=service,
                )
                update_kubernetes_secret_signature(
                    kube_client=kube_client,
                    secret=secret,
                    service=service,
                    secret_signature=signature,
                )
            else:
                log.info(f"{secret} for {service} up to date")

    with os.scandir(secret_dir) as secret_file_paths:
        for secret_file_path in secret_file_paths:
            if secret_file_path.path.endswith("json"):
                secret = secret_file_path.name.replace(".json", "")
                with open(secret_file_path, "r") as secret_file:
                    secret_data = json.load(secret_file)
                secret_signature = secret_provider.get_secret_signature_from_data(
                    secret_data
                )
                if secret_signature:
                    kubernetes_secret_signature = get_kubernetes_secret_signature(
                        kube_client=kube_client, secret=secret, service=service
                    )
                    if not kubernetes_secret_signature:
                        log.info(f"{secret} for {service} not found, creating")
                        try:
                            create_secret(
                                kube_client=kube_client,
                                secret=secret,
                                service=service,
                                secret_provider=secret_provider,
                            )
                        except ApiException as e:
                            if e.status == 409:
                                log.warning(
                                    f"Secret {secret} for {service} already exists"
                                )
                            else:
                                raise
                        create_kubernetes_secret_signature(
                            kube_client=kube_client,
                            secret=secret,
                            service=service,
                            secret_signature=secret_signature,
                        )
                    elif secret_signature != kubernetes_secret_signature:
                        log.info(
                            f"{secret} for {service} needs updating as signature changed"
                        )
                        update_secret(
                            kube_client=kube_client,
                            secret=secret,
                            service=service,
                            secret_provider=secret_provider,
                        )
                        update_kubernetes_secret_signature(
                            kube_client=kube_client,
                            secret=secret,
                            service=service,
                            secret_signature=secret_signature,
                        )
                    else:
                        log.info(f"{secret} for {service} up to date")
    return True


if __name__ == "__main__":
    main()
