#! /usr/bin/python

# Copyright (c) 2015 Intracom S.A. Telecom Solutions. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License v1.0 which accompanies this distribution,
# and is available at http://www.eclipse.org/legal/epl-v10.html

"""With this module we start the REST mininet server, that manages a mininet
topology"""

import argparse
import bottle
import json
import logging
import net.topologies

from net.multinet import Multinet

# We must define logging level separately because this module runs
# independently.
logging.basicConfig(level=logging.DEBUG)

MININET_TOPO = None


@bottle.route(
    '/init',
    method='POST')
def init():
    """
    Initializes a new topology object. The type of the new topology is
    defined by the topo parameter.
    Expects the topology configuration as JSON parameter.

    JSON entries:
        controller_ip_address (str): The IP address of the controller
        controller_of_port (int): The OpenFlow port of the controller
        switch_type (str): The type of the soft switch used for the emulation
        topo_type (str): The type of the topology
        topo_size (int): The size of the topology
        group_size (int): Size of groups for groupwise bootup
        group_delay (int): Delay in ms before the bootup of each group
        hosts_per_switch (int): The number of hosts per switch
        dpid_offset (int): The dpid offset for this VM
    """

    global MININET_TOPO

    topo_conf = bottle.request.json
    MININET_TOPO = Multinet(
        topo_conf['controller_ip_address'],
        int(topo_conf['controller_of_port']),
        topo_conf['switch_type'],
        topo_conf['topo_type'],
        int(topo_conf['topo_size']),
        int(topo_conf['group_size']),
        int(topo_conf['group_delay']),
        int(topo_conf['hosts_per_switch']),
        int(topo_conf['dpid_offset']),
        topo_conf['traffic_generation_duration_ms'],
        topo_conf['interpacket_delay_ms']
        )
    MININET_TOPO.init_topology()


@bottle.route('/start', method='POST')
def start():
    """
    Calls the start_topology() method of the current topology object to start
    the switches of the topology.
    """
    MININET_TOPO.start_topology()


@bottle.route('/detect_hosts', method='POST')
def detect_hosts():
    """
    Calls the detect_hosts() method of the current topology object to make
    the hosts visible in the controller side
    """
    MININET_TOPO.detect_hosts()


@bottle.route('/get_switches', method='POST')
def get_switches():
    """
    Calls the get_switches() method of the current topology object to query the
    current number of switches.

    Returns
        str: A JSON string with dpid_offset/number_of_switches key/value pairs
    """
    dpid_key = 'dpid-{0}'.format(MININET_TOPO._dpid_offset)
    num_sw = MININET_TOPO.get_switches()
    return json.dumps({dpid_key: num_sw})

@bottle.route('/get_flows', method='POST')
def get_flows():
    """
    Calls the get_flows() method of the current topology object to get the
    current number of flows installed on the switches.

    Returns
        str: A JSON string with dpid_offset/number_of_switches key/value pairs
    """
    dpid_key = 'number-of-flows-on-worker-{0}'.format(MININET_TOPO._dpid_offset)
    total_worker_flows = MININET_TOPO.get_flows()
    return json.dumps({dpid_key: total_worker_flows})

@bottle.route('/stop', method='POST')
def stop():
    """
    Calls the stop_topology() method of the current topology object to terminate
    the topology.
    """
    MININET_TOPO.stop_topology()


@bottle.route('/ping_all', method='POST')
def ping_all():
    """
    Calls the ping_all() method of the current topology object to issue
    all-to-all ping commands
    """
    MININET_TOPO.ping_all()

@bottle.route('/generate_traffic', method='POST')
def generate_traffic():
    """
    Calls the generate_traffic() method of the current topology object to
    generate traffic from the switches.
    """

    MININET_TOPO.generate_traffic()

def rest_start():
    """Starts Mininet REST server"""
    parser = argparse.ArgumentParser()
    parser.add_argument('--rest-host',
                        required=True,
                        type=str,
                        dest='rest_host',
                        action='store',
                        help='IP address to start Mininet REST server')
    parser.add_argument('--rest-port',
                        required=True,
                        type=str,
                        dest='rest_port',
                        action='store',
                        help='Port number to start Mininet REST server')
    args = parser.parse_args()

    bottle.run(host=args.rest_host, port=args.rest_port, debug=True)

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    rest_start()
