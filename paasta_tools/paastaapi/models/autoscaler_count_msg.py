# coding: utf-8

"""
    Paasta API

    No description provided (generated by Openapi Generator https://github.com/openapitools/openapi-generator)  # noqa: E501

    The version of the OpenAPI document: 1.0.0
    Generated by: https://openapi-generator.tech
"""


import pprint
import re  # noqa: F401

import six

from paasta_tools.paastaapi.configuration import Configuration


class AutoscalerCountMsg(object):
    """NOTE: This class is auto generated by OpenAPI Generator.
    Ref: https://openapi-generator.tech

    Do not edit the class manually.
    """

    """
    Attributes:
      openapi_types (dict): The key is attribute name
                            and the value is attribute type.
      attribute_map (dict): The key is attribute name
                            and the value is json key in definition.
    """
    openapi_types = {
        'calculated_instances': 'int',
        'desired_instances': 'int',
        'status': 'str'
    }

    attribute_map = {
        'calculated_instances': 'calculated_instances',
        'desired_instances': 'desired_instances',
        'status': 'status'
    }

    def __init__(self, calculated_instances=None, desired_instances=None, status=None, local_vars_configuration=None):  # noqa: E501
        """AutoscalerCountMsg - a model defined in OpenAPI"""  # noqa: E501
        if local_vars_configuration is None:
            local_vars_configuration = Configuration()
        self.local_vars_configuration = local_vars_configuration

        self._calculated_instances = None
        self._desired_instances = None
        self._status = None
        self.discriminator = None

        if calculated_instances is not None:
            self.calculated_instances = calculated_instances
        if desired_instances is not None:
            self.desired_instances = desired_instances
        if status is not None:
            self.status = status

    @property
    def calculated_instances(self):
        """Gets the calculated_instances of this AutoscalerCountMsg.  # noqa: E501


        :return: The calculated_instances of this AutoscalerCountMsg.  # noqa: E501
        :rtype: int
        """
        return self._calculated_instances

    @calculated_instances.setter
    def calculated_instances(self, calculated_instances):
        """Sets the calculated_instances of this AutoscalerCountMsg.


        :param calculated_instances: The calculated_instances of this AutoscalerCountMsg.  # noqa: E501
        :type calculated_instances: int
        """

        self._calculated_instances = calculated_instances

    @property
    def desired_instances(self):
        """Gets the desired_instances of this AutoscalerCountMsg.  # noqa: E501


        :return: The desired_instances of this AutoscalerCountMsg.  # noqa: E501
        :rtype: int
        """
        return self._desired_instances

    @desired_instances.setter
    def desired_instances(self, desired_instances):
        """Sets the desired_instances of this AutoscalerCountMsg.


        :param desired_instances: The desired_instances of this AutoscalerCountMsg.  # noqa: E501
        :type desired_instances: int
        """

        self._desired_instances = desired_instances

    @property
    def status(self):
        """Gets the status of this AutoscalerCountMsg.  # noqa: E501


        :return: The status of this AutoscalerCountMsg.  # noqa: E501
        :rtype: str
        """
        return self._status

    @status.setter
    def status(self, status):
        """Sets the status of this AutoscalerCountMsg.


        :param status: The status of this AutoscalerCountMsg.  # noqa: E501
        :type status: str
        """

        self._status = status

    def to_dict(self):
        """Returns the model properties as a dict"""
        result = {}

        for attr, _ in six.iteritems(self.openapi_types):
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = list(map(
                    lambda x: x.to_dict() if hasattr(x, "to_dict") else x,
                    value
                ))
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(map(
                    lambda item: (item[0], item[1].to_dict())
                    if hasattr(item[1], "to_dict") else item,
                    value.items()
                ))
            else:
                result[attr] = value

        return result

    def to_str(self):
        """Returns the string representation of the model"""
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        """For `print` and `pprint`"""
        return self.to_str()

    def __eq__(self, other):
        """Returns true if both objects are equal"""
        if not isinstance(other, AutoscalerCountMsg):
            return False

        return self.to_dict() == other.to_dict()

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        if not isinstance(other, AutoscalerCountMsg):
            return True

        return self.to_dict() != other.to_dict()