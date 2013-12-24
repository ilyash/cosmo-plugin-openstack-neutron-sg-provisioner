# vim: ts=4 sw=4 et

# Standard
import json
import os

# Celery
from celery import task

# OpenStack
import keystoneclient.v2_0.client as ksclient
from neutronclient.neutron import client

# Cosmo
from cosmo.events import send_event

@task
def provision(__cloudify_id, security_group, **kwargs):
    neutron_client = _init_client()
    if _get_security_group_by_name(neutron_client, security_group['name']):
        raise RuntimeError("Can not provision security group with name '{0}' because security group with such name already exists"
                           .format(security_group['name']))

    neutron_client.create_security_group({
        'security_group': {
            'name': security_group['name'],
        }
    })
    send_event(__cloudify_id, "sg-" + security_group['name'], "security group status", "state", "running")

@task
def terminate(security_group, **kwargs):
    neutron_client = _init_client()
    net = _get_security_group_by_name(neutron_client, security_group['name'])
    neutron_client.delete_security_group(net['id'])


# TODO: cache the token, cache client
def _init_client():
    config_path = os.getenv('NEUTRON_CONFIG_PATH', os.path.expanduser('~/neutron_config.json'))
    with open(config_path) as f:
        neutron_config = json.loads(f.read())

    keystone_client = _init_keystone_client()

    neutron_client = client.Client('2.0', endpoint_url=neutron_config['url'], token=keystone_client.auth_token)
    neutron_client.format = 'json'
    return neutron_client


def _init_keystone_client():
    config_path = os.getenv('KEYSTONE_CONFIG_PATH', os.path.expanduser('~/keystone_config.json'))
    with open(config_path) as f:
        cfg = json.loads(f.read())
    # Not the same config as nova client. Same parameters, different names.
    args = {field: cfg[field] for field in ('username', 'password', 'tenant_name', 'auth_url')}
    return ksclient.Client(**args)


def _get_security_group_by_name(neutron_client, name):
    # TODO: check whether neutron_client can get security_groups only named `name`
    matching_security_groups = neutron_client.list_security_groups(name=name)['security_groups']

    if len(matching_security_groups) == 0:
        return None
    if len(matching_security_groups) == 1:
        return matching_security_groups[0]
    raise RuntimeError("Lookup of security group by name failed. There are {0} security groups named '{1}'"
                       .format(len(matching_security_groups), name))


def _get_security_group_by_name_or_fail(neutron_client, name):
    security_group = _get_security_group_by_name(neutron_client, name)
    if security_group:
        return security_group
    raise ValueError("Lookup of security group by name failed. Could not find a security group with name {0}".format(name))


if __name__ == '__main__':
    neutron_client = _init_client()
    json.dumps(neutron_client.list_security_groups(), indent=4, sort_keys=True)
