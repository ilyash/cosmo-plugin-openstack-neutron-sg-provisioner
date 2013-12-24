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

    def test_all(self):
        name = self.name_prefix + 'net1'
        security_group = {'name': name}

        tasks.provision(name, security_group)
        security_group = tasks._get_security_group_by_name(self.neutron_client, name)
        self.assertIsNotNone(security_group)

        tasks.terminate(security_group)
        security_group = tasks._get_security_group_by_name(self.neutron_client, name)
        self.assertIsNone(security_group)


if __name__ == '__main__':
    unittest.main()
