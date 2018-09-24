# coding=utf-8
# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#
# Code generated by Microsoft (R) AutoRest Code Generator.
# Changes may cause incorrect behavior and will be lost if the code is
# regenerated.
# --------------------------------------------------------------------------

from .sub_resource import SubResource


class AzureFirewallIPConfiguration(SubResource):
    """IP configuration of an Azure Firewall.

    Variables are only populated by the server, and will be ignored when
    sending a request.

    :param id: Resource ID.
    :type id: str
    :param private_ip_address: The Firewall Internal Load Balancer IP to be
     used as the next hop in User Defined Routes.
    :type private_ip_address: str
    :param subnet: Reference of the subnet resource. This resource must be
     named 'AzureFirewallSubnet'.
    :type subnet: ~azure.mgmt.network.v2018_08_01.models.SubResource
    :param public_ip_address: Reference of the PublicIP resource. This field
     is a mandatory input if subnet is not null.
    :type public_ip_address:
     ~azure.mgmt.network.v2018_08_01.models.SubResource
    :param provisioning_state: The provisioning state of the resource.
     Possible values include: 'Succeeded', 'Updating', 'Deleting', 'Failed'
    :type provisioning_state: str or
     ~azure.mgmt.network.v2018_08_01.models.ProvisioningState
    :param name: Name of the resource that is unique within a resource group.
     This name can be used to access the resource.
    :type name: str
    :ivar etag: A unique read-only string that changes whenever the resource
     is updated.
    :vartype etag: str
    """

    _validation = {
        'etag': {'readonly': True},
    }

    _attribute_map = {
        'id': {'key': 'id', 'type': 'str'},
        'private_ip_address': {'key': 'properties.privateIPAddress', 'type': 'str'},
        'subnet': {'key': 'properties.subnet', 'type': 'SubResource'},
        'public_ip_address': {'key': 'properties.publicIPAddress', 'type': 'SubResource'},
        'provisioning_state': {'key': 'properties.provisioningState', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'etag': {'key': 'etag', 'type': 'str'},
    }

    def __init__(self, **kwargs):
        super(AzureFirewallIPConfiguration, self).__init__(**kwargs)
        self.private_ip_address = kwargs.get('private_ip_address', None)
        self.subnet = kwargs.get('subnet', None)
        self.public_ip_address = kwargs.get('public_ip_address', None)
        self.provisioning_state = kwargs.get('provisioning_state', None)
        self.name = kwargs.get('name', None)
        self.etag = None