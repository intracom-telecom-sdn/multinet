# Copyright (c) 2015 Intracom S.A. Telecom Solutions. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License v1.0 which accompanies this distribution,
# and is available at http://www.eclipse.org/legal/epl-v10.html

"""
Builds on Mininet to emulate large-scale SDN networks
by creating distributed Mininet topologies
"""

import logging
import time
import mininet
import mininet.util
import mininet.net
import mininet.node
import mininet.link
import mininet.clean
import itertools
import net.topologies
import socket
import struct

logging.basicConfig(level=logging.DEBUG)


class Multinet(mininet.net.Mininet):

    """
    Superclass representing a Mininet topology that is being booted in custom
    way. Switches are being added in groups with certain delay between each
    group.
    """

    """
    name - class correspondence for the topologies
    """
    TOPOS = {
        'disconnected': net.topologies.DisconnectedTopo,
        'linear': net.topologies.LinearTopo,
        'ring': net.topologies.RingTopo,
        'mesh': net.topologies.MeshTopo
    }

    """
    name - class correspondence for the soft switches
    """
    SWITCH_CLASSES = {
        'ovsk': mininet.node.OVSKernelSwitch,
        'user': mininet.node.UserSwitch
    }

    def __init__(self, controller_ip, controller_port, switch_type, topo_type,
                 num_switches, group_size, group_delay_ms, hosts_per_switch,
                 dpid_offset, traffic_generation_duration_ms,
                 interpacket_delay_ms, auto_detect_hosts=False):
        """
        Call the super constructor and initialize any extra properties we want to user

        Args:
            controller_ip (str): The IP address of the RemoteController
            controller_port (int): The OpenFlow port of the RemoteController
            switch_type (str): The type of the soft switch to use for the emulation
            topo_type (str): The type of the topology to build
            num_switches (int): The number of the switches in the topology
            group_size (int): The number of switches in a gorup for gradual bootup
            group_delay_ms (int): The delay between the bootup of each group
            hosts_per_switch (int): The number of hosts connected to each switch
            dpid_offset (int): The dpid offset of this worker
            traffic_generation_duration_ms (int): The interval of time, during
                                                  which transmission of
                                                  Packet_IN's occures
            interpacket_delay_ms (int): The interval of time between 2
                                        Packet_IN transmissions
            auto_detect_hosts (bool): Enable or disable automatic host detection
        """
        self.__network_mask_bits = 8
        self.__base_network = '10.0.0.0'
        self.__network_ip_range = long(2 ** (32 - self.__network_mask_bits))
        self.__available_networks = long(2 ** self.__network_mask_bits -
            (self.ip2long(self.__base_network) / self.__network_ip_range))
        # Initialize the Mininet network of the worker, based on the dpid.
        # Each worker has its own network.
        if dpid_offset <= self.__available_networks:
            self.__mininet_network = self.long2ip(
                self.ip2long(self.__base_network) +
                (dpid_offset * self.__network_ip_range))
        else:
            error('Worker Mininet network is out of range.')
            raise ValueError('Worker Mininet network is out of range.')

        self._topo_type = topo_type
        self._num_switches = num_switches
        self._dpid_offset = dpid_offset
        self._group_size = group_size
        self._group_delay = float(group_delay_ms) / 1000
        self._hosts_per_switch = hosts_per_switch
        self.auto_detect_hosts = auto_detect_hosts
        self._controller_ip = controller_ip
        self._controller_port = controller_port
        self.booted_switches = 0
        self._traffic_generation_duration_ms = traffic_generation_duration_ms
        self._interpacket_delay_ms = interpacket_delay_ms

        super(
            Multinet,
            self).__init__(
            topo=self.TOPOS[
                self._topo_type](
                k=self._num_switches,
                n=self._hosts_per_switch,
                dpid=self._dpid_offset),
            switch=self.SWITCH_CLASSES[switch_type],
            host=mininet.node.Host,
            controller=mininet.node.RemoteController,
            link=mininet.link.Link,
            intf=mininet.link.Intf,
            build=False,
            xterms=False,
            cleanup=False,
            ipBase=self.__mininet_network + '/' + str(self.__network_mask_bits),
            inNamespace=False,
            autoSetMacs=False,
            autoStaticArp=False,
            autoPinCpus=False,
            listenPort=6634,
            waitConnected=False)
        self.ipBaseNum += self._dpid_offset

    def buildFromTopo(self, topo=None):
        """
        Build mininet from a topology object
        At the end of this function, everything should be connected and up.
        Use the dpid offset to distinguise the nodes between Multinet Instances
        """

        info = logging.info
        # Possibly we should clean up here and/or validate
        # the topo
        if self.cleanup:
            pass

        info('*** Creating network\n')

        if not self.controllers and self.controller:
            # Add a default controller
            info('*** Adding controller\n')
            try:
                classes = self.controller
                if not isinstance(classes, list):
                    classes = [classes]
                for i, cls in enumerate(classes):
                    # Allow Controller objects because nobody understands partial()
                    if isinstance(cls, mininet.node.Controller):
                        self.addController(controller=cls,
                                           ip=self._controller_ip,
                                           port=self._controller_port)
                    else:
                        self.addController(name='c{0}'.format(i),
                                           controller=cls,
                                           ip=self._controller_ip,
                                           port=self._controller_port)
            except:
                self.addController(name='c{0}'.format(i), controller=mininet.node.DefaultController)

        info('*** Adding hosts:\n')
        for hostName in topo.hosts():
            kwargs_host = topo.nodeInfo(hostName)
            self.addHost(hostName, **kwargs_host)
            info(hostName + ' ')

        info('\n*** Adding switches:\n')
        for switchName in topo.switches():
            # A bit ugly: add batch parameter if appropriate
            params = topo.nodeInfo(switchName)
            cls = params.get('cls', self.switch)
            params['dpid'] = None
            params['protocols'] = 'OpenFlow13'
            #if hasattr(cls, 'batchStartup'):
            #    params.setdefault('batch', True)
            self.addSwitch(switchName, **params)
            info(switchName + ' ')

        info('\n*** Adding links:\n')
        for srcName, dstName, params in topo.links(
                sort=True, withInfo=True):
            self.addLink(**params)
            info('(%s, %s) ' % (srcName, dstName))

        info('\n')

    def init_topology(self):
        """
        Init the topology
        """

        logging.info("[mininet] Initializing topology.")
        self.build()
        logging.info('[mininet] Topology initialized successfully. '
                     'Booted up {0} switches'.format(self._num_switches))


    def start_topology(self):
        """
        Start controller and switches.
        Do a gradual bootup.
        """
        info = logging.info
        if not self.built:
            self.build()
        info('*** Starting controller\n')
        for controller in self.controllers:
            info(controller.name + ' ')
            controller.start()
        info('\n')
        info('*** Starting %s switches\n' % len(self.switches))

        for ind, switch in enumerate(self.switches):
            if ind % self._group_size == 0:
                time.sleep(self._group_delay)
            logging.debug('[mininet] Starting switch with index {0}'.
                          format(ind + 1))
            info(switch.name + ' ')
            switch.start(self.controllers)
            self.booted_switches += 1

        started = {}
        for swclass, switches in itertools.groupby(
                sorted(self.switches, key=type), type):
            switches = tuple(switches)
            if hasattr(swclass, 'batchStartup'):
                success = swclass.batchStartup(switches)
                started.update({s: s for s in success})
        info('\n')
        if self.waitConn:
            self.waitConnected()

        logging.info('[mininet] Topology started successfully. '
                     'Booted up {0} switches'.format(self._num_switches))
        time.sleep(self._group_delay * 2)

        if self.auto_detect_hosts:
            self.detect_hosts(ping_cnt=50)


    def detect_hosts(self, ping_cnt=50):
        """
        Do a ping from each host to the void to send a PACKET_IN to the controller
        and enable the controller host detector

        Args:
            ping_cnt: Number of pings to send from each host
        """
        for host in self.hosts:
            # ping the void
            host.sendCmd('ping -c{0} {1}'.format(str(ping_cnt),
                                                 str(self.controllers[0].IP())))

        logging.debug('[mininet] Hosts should be visible now')

    def get_switches(self):
        """Returns the total number of switches of the topology

        Returns:
            (int): number of switches in the topology
        """
        return self.booted_switches

    def stop_topology(self):
        """
        Stops the topology
        """

        logging.info('[mininet] Halting topology. Terminating switches.')
        for h in self.hosts:
            h.sendInt()
        mininet.clean.cleanup()
        self.switches = []
        self.hosts = []
        self.links = []
        self.controllers = []
        self.built = False
        self.booted_switches = 0
        logging.info('[mininet] Topology halted successfully')


    def ping_all(self):
        """
        All-to-all host pinging used for testing.
        """
        self.pingAll(timeout=None)


    def get_flows(self):
        """
        Getting flows from switches
        """
        logging.info('[get_flows] Getting flows from switches.')
        flow_number_total = 0
        for switch in self.switches:
            flows_list = switch.dpctl('-O OpenFlow13 dump-flows').split('\n')
            flow_number = len(flows_list) - 2
            flow_number_total += flow_number

        logging.debug('[get_flows] number of flows: {0}'.format(flow_number_total))
        return flow_number_total


    def generate_mac_address_pairs(self, current_mac):
        """
        Generated tuple of source/destination mac addressess

        Args:
          current_mac (str): The last generated mac used for traffic
                             generation. It is used as reference to generate
                             the next pair of source and destination mac
                             addresses.
        """

        # We place an extra 11 in front of base_mac and these digits are
        # filtered out, in order to get a full range of mac addresses. We get
        # generated mac addresses as string separated with : for every 2
        # characters.
        base_mac = 0x11000000000000
        generated_mac = hex(base_mac + int(current_mac, 16))

        source_mac = ':'.join(''.join(pair) for pair in zip(*[iter(hex(int(generated_mac, 16) + 1))]*2))[6:]
        dest_mac = ':'.join(''.join(pair) for pair in zip(*[iter(hex(int(generated_mac, 16) + 2))]*2))[6:]
        return source_mac, dest_mac

    def generate_traffic(self):
        """
        Traffic generation from switches to controller
        """

        logging.info('[mininet] Generating traffic from switches.')

        if not self._hosts_per_switch>1:
            raise AssertionError(
                '_hosts_per_switch must be at least 2 or greater.')
        traffic_transmission_delay = self._interpacket_delay_ms / 1000
        traffic_transmission_interval = \
            self._traffic_generation_duration_ms / 1000
        host_index = 0

        transmission_start = time.time()
        last_mac = hex(int(hex(self._dpid_offset) + '00000000', 16) + 0xffffffff)
        last_ip = self.ip2long('255.255.255.253')
        current_mac = hex(int(last_mac, 16) - 0x0000ffffffff + 0x000000000001)
        current_ip = self.ip2long('{0}.0.0.1'.format(self._dpid_offset))

        while (time.time() - transmission_start) <= traffic_transmission_interval:
            src_mac, dst_mac = self.generate_mac_address_pairs(current_mac)
            arp_ip_h1 = self.long2ip(current_ip)
            arp_ip_h2 = self.long2ip(current_ip + 1)
            current_mac = hex(int(current_mac, 16) + 2)
            current_ip += 2
            self.hosts[host_index].sendCmd(
                'sudo mz -a {0} -b {1} -t arp "targetmac={2}, sendermac={3}, targetip={4}, senderip={5}"'.
                format(src_mac, dst_mac, 'ff:ff:ff:ff:ff:ff', src_mac, arp_ip_h1, arp_ip_h1))
            self.hosts[host_index + 1].sendCmd(
                'sudo mz -a {0} -b {1} -t arp "targetmac={2}, sendermac={3}, targetip={4}, senderip={5}"'.
                format(dst_mac, src_mac, 'ff:ff:ff:ff:ff:ff', dst_mac, arp_ip_h2, arp_ip_h2))
            time.sleep(traffic_transmission_delay)
            host_index += self._hosts_per_switch

            if host_index >= len(self.hosts):
                for host in self.hosts:
                    host.waitOutput()
                host_index = 0

            if current_ip >= last_ip:
                current_ip = self.ip2long('{0}.0.0.1'.format(self._dpid_offset))

            if int(current_mac, 16) >= int(last_mac, 16):
                current_mac = \
                    hex(int(last_mac, 16) - 0x0000ffffffff + 0x000000000001)
                # The minimum controller hard_timeout is 1 second.
                # Retransmission using the init_mac must start after the
                # minimum hard_timeout interval
                if (time.time - transmission_start) < 1:
                    time.sleep(1 - (time.time - transmission_start))
        # Cleanup hosts console outputs and write flags after finishing
        # transmission
        for host in self.hosts:
            host.waitOutput()

    def ip2long(self, ip_str):
        """
        Convert an IP string to long number
        Args:
            ip_str (str): IP address as a string
        """
        packedIP = socket.inet_aton(ip_str)
        return struct.unpack("!L", packedIP)[0]

    def long2ip(self, ip_lng):
        """
        Convert long number to IP string
        Args:
            ip_lng (long): IP address as a long number
        """
        return socket.inet_ntoa(struct.pack('!L', ip_lng))
