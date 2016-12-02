#!/usr/bin/env python2
import logging
import shade
import time
import re


class Regulator(object):

    def __init__(self, server_count=1):

        # logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        # set variables
        self.server_count = server_count
        self.name_prefix = 'pst-'
        self.check_sleep = 5
        self.hosts_file = './hosts'

        # shade config
        self.openstack_cloud = 'ovh'
        self.openstack_flavor = 'vps-ssd-1'
        self.openstack_image = 'Ubuntu 16.04'
        self.openstack_meta = {'Subject': 'pst'}
        self.openstack_keypair = 'yubi'
        self.openstack_security_groups = ['pst']
        self.openstack_userdata = """#!/usr/bin/env bash
            apt-get install -y python
            date > /root/install
            """

        # state variables
        self.servers = {}
        self.allowed_servers = []

        # run once
        self.init_shade()
        self.generate_servers()
        self.load_servers()
        self.start_servers()
        self.stop_servers()
        self.wait_for_servers()
        self.print_dns()
        self.write_hosts()

    def init_shade(self):
        """Initialize shade library"""
        shade.simple_logging(debug=True)

        self.cloud = shade.openstack_cloud(cloud=self.openstack_cloud)
        self.instance_image = self.cloud.get_image(self.openstack_image)
        self.instance_flavor = self.cloud.get_flavor(
            self.openstack_flavor,
            get_extra=False
        )

    def generate_servers(self):
        """Generate required server names"""
        for i in range(0, self.server_count):
            name = self.name_prefix + str(i)
            self.allowed_servers.append(name)
            if name not in self.servers:
                self.servers[name] = {}

    def load_servers(self):
        """Load running servers"""
        for i in self.cloud.list_servers():
            if re.match(r'^' + self.name_prefix + '.*$', i.name):
                self.servers[i.name] = i

    def start_servers(self):
        """Start servers which are not started yet"""
        for name, config in self.servers.items():
            print(name)
            print(config)
            if not config:
                self.create_server(name)

    def stop_servers(self, wait=False):
        """Stop servers which should not be running"""
        for name, config in self.servers.items():
            if name not in self.allowed_servers:
                self.cloud.delete_server(config['id'], wait)
                del self.servers[name]

    def create_server(self, name):
        """Start server and set name"""

        self.cloud.create_server(
            name,
            self.instance_image,
            self.instance_flavor,
            terminate_volume=True,
            meta=self.openstack_meta,
            key_name=self.openstack_keypair,
            userdata=self.openstack_userdata,
            security_groups=self.openstack_security_groups,
        )

    def wait_for_servers(self):
        """Wait for servers to be in active state"""

        while not self.servers_running():
            time.sleep(self.check_sleep)

    def servers_running(self):
        """All servers are running"""

        self.load_servers()

        all_active = True

        for name, config in self.servers.items():
            if name in self.allowed_servers:
                if config:
                    print('{} in state {}'.format(name, config['vm_state']))
                    if config['vm_state'] != 'active':
                        all_active = False
                else:
                    print('{} not created yet'.format(name))
                    all_active = False

        return all_active

    def print_dns(self):
        """Print IP addresses for DNS"""
        print('----')
        for name, config in self.servers.items():
            if name in self.allowed_servers:
                print('{}\tIN\tA\t {}'.format(
                    name,
                    config['addresses']['Ext-Net'][0]['addr']
                ))
        print('----')

    def write_hosts(self):
        """Write hosts to hosts file (Ansible)"""
        f = open(self.hosts_file, 'w')

        for name, config in self.servers.items():
            if name in self.allowed_servers:
                line = "{} ansible_host={}\n".format(
                    name,
                    config['addresses']['Ext-Net'][0]['addr']
                )
                f.write(line)

        f.close()


if __name__ == '__main__':
    print('Running as script ...')

    servers = 1

    a = Regulator(servers)
