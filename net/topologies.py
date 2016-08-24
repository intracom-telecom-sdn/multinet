"""
Modified Topologies created with the High Level Mininet API
"""

from mininet.topo import Topo
import random
import socket
import string
import struct


def genHostName(i, j, dpid, n, k):
    """Generate the host name
    Args:
        i (int): The switch number
        j (int): The host number
        dpid (int): The dpid offset
        n (int): The number of hosts per switch
        k (int): number of switches

    Returns:
        str: The host name
    """
    name_prefix_list = list(string.ascii_lowercase + string.ascii_uppercase)
    worker_id = dpid
    host_index_offset = worker_id * k * n
    if not ((j + i*n + host_index_offset)//999 < len(name_prefix_list)):
        raise AssertionError('Reached maximum number of hosts')
    return ('{0}{1}'.
                     format(name_prefix_list[(j + i*n + host_index_offset)//999],
                            (j + i*n + host_index_offset)%999))

def genSwitchName(i, dpid, k):
    """Generate the switch name
    Args:
        i (int): The switch number
        dpid (int): The dpid offset
        k (int): number of switches
    Returns:
        str: The switch name
    """
    worker_id = dpid
    switch_id = (worker_id * k) + i
    if switch_id > 9999:
        raise AssertionError('Reached maximum number of switches')
    #return '{0}{1}'.format(name_prefix_list[(i + dpid)//999], (i + dpid)%999)
    return '{0}'.format(switch_id)

class IpAddressGenerator():
    """ IP address generator class. Generates IP addresses inside a Network
    that is relevant to a base Network defined in initialization."""

    def __init__(self, dpid):
        self.network_mask_bits = 8
        self.__base_network = '10.0.0.0'
        self.__network_ip_range = 2 ** (32 - self.network_mask_bits)
        self.__next_ip_index = 0
        self.__available_networks = int(2 ** self.network_mask_bits -
            (self.ip2long(self.__base_network) / self.__network_ip_range))
        # Initialize the Mininet network of the worker, based on the dpid.
        # Each worker has its own network.
        if dpid <= self.__available_networks:
            self.mininet_network = self.long2ip(self.ip2long(self.__base_network) +
                (dpid * self.__network_ip_range))
        else:
            raise ValueError('Worker Mininet network is out of range.')

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

    def generate_cidr_ip(self):
        """
        Generates the next IP address with CIDR format inside the Mininet
        network of the worker. Each worker has its own network, depend on
        its dpid.
        """
        self.__next_ip_index += 1
        if self.__next_ip_index <= (self.__network_ip_range - 2):
            next_lng_ip = self.ip2long(self.mininet_network) + self.__next_ip_index
            return {'ip_addr':self.long2ip(next_lng_ip),
                    'net_mask':self.network_mask_bits}
        else:
            raise ValueError('Hosts IP addresses are out of range.')

class LinearTopo(Topo):
    "Linear topology of k switches, with n hosts per switch."

    def build(self, k=2, n=1, dpid=1, **_opts):
        """k: number of switches
           n: number of hosts per switch"""
        self.k = k
        self.n = n
        ip_generator = IpAddressGenerator(dpid)
        lastSwitch = None

        for i in xrange(k):
            # Add switch
            switch = self.addSwitch(genSwitchName(i, dpid, k))
            # Add hosts to switch
            for j in xrange(n):
                host = self.addHost(genHostName(i, j, dpid, n, k))
                cidr_ip = ip_generator.generate_cidr_ip()
                self.g.node[host].setIP(cidr_ip['ip_addr'], cidr_ip['net_mask'])
                self.addLink(host, switch)
            # Connect switch to previous
            if lastSwitch:
                self.addLink(switch, lastSwitch)
            lastSwitch = switch
        del ip_generator


class RingTopo(Topo):
    "Ring topology of k switches, with n hosts per switch."

    def build(self, k=2, n=1, dpid=1, **_opts):
        """k: number of switches
           n: number of hosts per switch"""
        self.k = k
        self.n = n
        ip_generator = IpAddressGenerator(dpid)
        lastSwitch = None
        firstSwitch = None

        for i in xrange(k):
            # Add switch
            switch = self.addSwitch(genSwitchName(i, dpid, k))
            if i == 0:
                firstSwitch = switch
            # Add hosts to switch
            for j in xrange(n):
                host = self.addHost(genHostName(i, j, dpid, n, k))
                cidr_ip = ip_generator.generate_cidr_ip()
                self.g.node[host].setIP(cidr_ip['ip_addr'], cidr_ip['net_mask'])
                self.addLink(host, switch)
            # Connect switch to previous
            if lastSwitch:
                self.addLink(switch, lastSwitch)
            lastSwitch = switch
        self.addLink(lastSwitch, firstSwitch)
        del ip_generator


class DisconnectedTopo(Topo):
    "Disconnected topology of k switches, with n hosts per switch."

    def build(self, k=2, n=1, dpid=1, **_opts):
        """k: number of switches
           n: number of hosts per switch"""
        self.k = k
        self.n = n
        ip_generator = IpAddressGenerator(dpid)

        for i in xrange(k):
            # Add switch
            switch = self.addSwitch(genSwitchName(i, dpid, k))
            # Add hosts to switch
            for j in xrange(n):
                host = self.addHost(genHostName(i, j, dpid, n, k))
                cidr_ip = ip_generator.generate_cidr_ip()
                self.g.node[host].setIP(cidr_ip['ip_addr'], cidr_ip['net_mask'])
                self.addLink(host, switch)
        del ip_generator


class MeshTopo(Topo):
    "Mesh topology of k switches, with n hosts per switch."

    def build(self, k=2, n=1, dpid=1, **_opts):
        """k: number of switches
           n: number of hosts per switch"""
        self.k = k
        self.n = n
        ip_generator = IpAddressGenerator(dpid)
        prevSwitches = []

        for i in xrange(k):
            # Add switch
            switch = self.addSwitch(genSwitchName(i, dpid, k))
            # Add hosts to switch
            for j in xrange(n):
                host = self.addHost(genHostName(i, j, dpid, n, k))
                cidr_ip = ip_generator.generate_cidr_ip()
                self.g.node[host].setIP(cidr_ip['ip_addr'], cidr_ip['net_mask'])
                self.addLink(host, switch)
            # Connect switch to previous
            for prevSwitch in prevSwitches:
                self.addLink(switch, prevSwitch)
            prevSwitches.append(switch)
        del ip_generator



