#!/usr/bin/env python
# vim: ts=4 sw=4 et
import logging
import mock
import random
import string
import unittest

import cosmo.events
cosmo.events.send_event = mock.Mock()
import openstack_neutron_sg_provisioner.tasks as tasks

RANDOM_LEN = 3  # cosmo_test_neutron_XXX_something


class OpenstackSecurityGroupProvisionerTestCase(unittest.TestCase):

    def setUp(self):
        logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.level = logging.DEBUG
        self.logger.info("setUp called")
        self.neutron_client = tasks._init_client()
        self.name_prefix = 'cosmo_test_neutron_{0}_'.format(''.join(
            [random.choice(string.ascii_uppercase + string.digits) for i in range(RANDOM_LEN)]
        ))

    def tearDown(self):
        for net in self.neutron_client.list_security_groups()['security_groups']:
            if net['name'].startswith(self.name_prefix):
                self.neutron_client.delete_security_group(net['id'])

    def rules_for_sg_id(self, id):
        rules = self.neutron_client.list_security_group_rules()['security_group_rules']
        rules = [rule for rule in rules if rule['security_group_id'] == id]
        return rules

    def test_sg_provision_and_terminate(self):
        name = self.name_prefix + 'sg1'
        security_group = {
            'name': name,
            'rules': [],
        }

        tasks.provision(name, security_group)
        security_group = tasks._get_security_group_by_name(self.neutron_client, name)
        self.assertIsNotNone(security_group)

        # Must have 2 egress rules by default
        rules = self.rules_for_sg_id(security_group['id'])
        egress_rules_count = sum([rule['direction'] == 'egress' for rule in rules])
        self.assertEquals(egress_rules_count, 2)

        tasks.terminate(security_group)
        security_group = tasks._get_security_group_by_name(self.neutron_client, name)
        self.assertIsNone(security_group)

    def test_disabled_egress_sg(self):
        name = self.name_prefix + 'sg2'
        security_group = {
            'name': name,
            'rules': [],
            'disable_egress': True,
        }

        tasks.provision(name, security_group)
        security_group = tasks._get_security_group_by_name(self.neutron_client, name)
        self.assertIsNotNone(security_group)

        # Must have no egress rules
        rules = self.rules_for_sg_id(security_group['id'])
        egress_rules_count = sum([rule['direction'] == 'egress' for rule in rules])
        self.assertEquals(egress_rules_count, 0)

    def test_single_egress_rule_sg(self):
        name = self.name_prefix + 'sg3'
        security_group = {
            'name': name,
            'rules': [{
                'direction': 'egress'
            }],
        }

        tasks.provision(name, security_group)
        security_group = tasks._get_security_group_by_name(self.neutron_client, name)
        self.assertIsNotNone(security_group)

        # Must have 1 egress rule
        rules = self.rules_for_sg_id(security_group['id'])
        egress_rules_count = sum([rule['direction'] == 'egress' for rule in rules])
        self.assertEquals(egress_rules_count, 1)

    def test_egress_rule_plus_disabled_egress(self):
        name = self.name_prefix + 'sg4'
        security_group = {
            'name': name,
            'rules': [{
                'direction': 'egress'
            }],
            'disable_egress': True,
        }
        with self.assertRaises(RuntimeError):
            tasks.provision(name, security_group)


if __name__ == '__main__':
    unittest.main()
