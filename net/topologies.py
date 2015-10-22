"""
Modified Topologies created with the High Level Mininet API
"""
from mininet.topo import Topo


def genHostName(i, j, dpid, n):
    """Generate the host name
    Args:
        i (int): The switch number
        j (int): The host number
        dpid (int): The dpid offset
        n (int): The number of hosts per switch

    Returns:
        str: The host name
    """
    return 'h%d' % (j + i*n + dpid)

def genSwitchName(i, dpid):
    """Generate the switch name
    Args:
        i (int): The switch number
        dpid (int): The dpid offset

    Returns:
        str: The switch name
    """
    return 's%d' % (i + dpid)

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
            switch = self.addSwitch(genSwitchName(i, dpid))
            # Add hosts to switch
            for j in xrange(n):
                host = self.addHost(genHostName(i, j, dpid, n))
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
            switch = self.addSwitch(genSwitchName(i, dpid))
            if i == 0:
                firstSwitch = switch
            # Add hosts to switch
            for j in xrange(n):
                host = self.addHost(genHostName(i, j, dpid, n))
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
            switch = self.addSwitch(genSwitchName(i, dpid))
            # Add hosts to switch
            for j in xrange(n):
                host = self.addHost(genHostName(i, j, dpid, n))
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
            switch = self.addSwitch(genSwitchName(i, dpid))
            # Add hosts to switch
            for j in xrange(n):
                host = self.addHost(genHostName(i, j, dpid, n))
                self.addLink(host, switch)
            # Connect switch to previous
            for prevSwitch in prevSwitches:
                self.addLink(switch, prevSwitch)
            prevSwitches.append(switch)



