"""
Modified Topologies created with the High Level Mininet API
"""
from mininet.topo import Topo
import random
import string



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
    numeric_range = 999
    name_prefix = ''
    worker_id = dpid
    host_index_offset = worker_id * k * n
    alpharethmetic_range = (j + i*n + host_index_offset)//numeric_range
    while alpharethmetic_range >= 0:
        name_prefix += name_prefix_list[alpharethmetic_range % len(name_prefix_list)]
        alpharethmetic_range = (alpharethmetic_range // len(name_prefix_list)) - 1
    name_prefix = name_prefix[::-1]
    return ('{0}{1}'.
                     format(name_prefix,
                            (j + i*n + host_index_offset)%numeric_range))

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
    #if switch_id > 9999:
    #    raise AssertionError('Reached maximum number of switches')
    #return '{0}{1}'.format(name_prefix_list[(i + dpid)//999], (i + dpid)%999)
    return '{0}'.format(switch_id)

class LinearTopo(Topo):
    "Linear topology of k switches, with n hosts per switch."

    def build(self, k=2, n=1, dpid=1, **_opts):
        """k: number of switches
           n: number of hosts per switch"""
        self.k = k
        self.n = n

        lastSwitch = None
        for i in xrange(k):
            # Add switch
            switch = self.addSwitch(genSwitchName(i, dpid, k))
            # Add hosts to switch
            for j in xrange(n):
                host = self.addHost(genHostName(i, j, dpid, n, k))
                self.addLink(host, switch)
            # Connect switch to previous
            if lastSwitch:
                self.addLink(switch, lastSwitch)
            lastSwitch = switch


class RingTopo(Topo):
    "Ring topology of k switches, with n hosts per switch."

    def build(self, k=2, n=1, dpid=1, **_opts):
        """k: number of switches
           n: number of hosts per switch"""
        self.k = k
        self.n = n

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
                self.addLink(host, switch)
            # Connect switch to previous
            if lastSwitch:
                self.addLink(switch, lastSwitch)
            lastSwitch = switch
        self.addLink(lastSwitch, firstSwitch)


class DisconnectedTopo(Topo):
    "Disconnected topology of k switches, with n hosts per switch."

    def build(self, k=2, n=1, dpid=1, **_opts):
        """k: number of switches
           n: number of hosts per switch"""
        self.k = k
        self.n = n

        for i in xrange(k):
            # Add switch
            switch = self.addSwitch(genSwitchName(i, dpid, k))
            # Add hosts to switch
            for j in xrange(n):
                host = self.addHost(genHostName(i, j, dpid, n, k))
                self.addLink(host, switch)


class MeshTopo(Topo):
    "Mesh topology of k switches, with n hosts per switch."

    def build(self, k=2, n=1, dpid=1, **_opts):
        """k: number of switches
           n: number of hosts per switch"""
        self.k = k
        self.n = n

        prevSwitches = []
        for i in xrange(k):
            # Add switch
            switch = self.addSwitch(genSwitchName(i, dpid, k))
            # Add hosts to switch
            for j in xrange(n):
                host = self.addHost(genHostName(i, j, dpid, n, k))
                self.addLink(host, switch)
            # Connect switch to previous
            for prevSwitch in prevSwitches:
                self.addLink(switch, prevSwitch)
            prevSwitches.append(switch)



