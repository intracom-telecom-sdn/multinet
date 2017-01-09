"""
Multinet utility functions to communicate with the master and the worker machines
"""

import requests
import sys
import multiprocessing
import json
import time
import logging
import argparse


logging.getLogger().setLevel(logging.DEBUG)

def parse_arguments():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('--json-config',
                        required=True,
                        type=str,
                        dest='json_config',
                        action='store',
                        help='Configuration file (JSON)')

    parser.add_argument('--serial-requests',
                        required=False,
                        dest='is_serial',
                        action='store_true',
                        default=False,
                        help='Is request in serial execution mode')

    args = parser.parse_args()
    return args


def parse_json_conf(json_config):
    """Parse a JSON configuration file.
    The path to this file is given as a command line argument.

    Command Line Args:
      --json-config (str): The path to the JSON configuration file

    Returns:
      dict: The parsed json configuration
    """

    conf = {}
    with open(json_config) as conf_file:
        conf = json.load(conf_file)
    return conf


def dpid_offset_range(num_vms):
    """Generate a range of dpid dpid_offset_list
    Every VM has allocates 1000 unique dpid offsets

    Args:
      num_vms (int): The number of virtual machines
      topo_size (int): The number of topology switches
    Returns:
      list: The dpid offset range
    """
    return [i for i in xrange(0, num_vms)]


def make_post_request(host_ip, host_port, route, data=None):
    """Make a POST request
    Make a POST request to a remote REST server and log the response

    Args:
      host_ip (str): The ip of the remote REST server
      host_port (int): The port of the remote REST server
      route (str): The REST API endpoint
      data (dict): A dictionary or a list with any additional data

    Returns:
      requests.models.Response: The HTTP response for the performed request
    """
    session = requests.Session()
    session.trust_env = False

    url = 'http://{0}:{1}/{2}'.format(host_ip, host_port, route)
    route_name = route.split('/')[0]
    logging.info('[{0}_topology_handler][url] {1}'.format(route_name, url))
    if data is None:
        post_call = session.post(url)
    else:
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        post_call = session.post(
            url,
            data=json.dumps(data),
            headers=headers)
    logging.info('[{0}_topology_handler][response status code] {1}'.
          format(route_name, post_call.status_code))
    logging.info('[{0}_topology_handler][response data] {1}'.
          format(route_name, post_call.text))

    return post_call


def make_post_request_runner(host_ip, host_port, route, data, queue):
    """Wrapper function to create a new job for each POST request.
    Make a POST request and put the response in a queue.
    Used for multiprocessing.

    Args:
      host_ip (str): The IP address of the REST server
      host_port (int): The port of the REST server
      route (str): The REST API endpoint
      data (str): Any additional JSON data
      queue (multiprocessing.Queue): The queue where all the responses are stored
    """
    queue.put(make_post_request(host_ip, host_port, route, data))
    return 0


def handle_post_request(post_call, exit_on_fail=True):
    """Handle the response of a REST request
    If the status code is not successful and the caller specifies so, sys.exit
    Else log the response text

    Args:
      post_call (requests.models.Response): The response to handle
      exit_on_fail (Optional[bool]): True -> Exit on error status code / False -> continue
    """
    failed_post_call = post_call.status_code >= 300 or post_call.status_code < 200
    if failed_post_call and exit_on_fail:
        sys.exit(post_call.status_code)
    else:
        logging.debug(post_call.text)


def broadcast_cmd(worker_ip_list, worker_port_list, opcode, data=None):
    """Broadcast a POST request to all the workers
    Use multiple processes to send POST requests to a specified
    endpoint of all the workers simultaneously.

    Args:
      worker_ip_list (list): A list of IP addresses to broadcast the POST request
      worker_port (int): The port of the workers
      opcode (str): The REST API endpoint
      topo_size (int): The number of topology switches
      data (dict): JSON data to go with the request

    Returns:
      list: A list of responses for all the POST requests performed
    """

    if data is not None:
        is_serial = data['is_serial']
    else:
        logging.info('[{0}] POST data is None. Setting is_serial to False'.
                     format(opcode))
        is_serial = False

    if opcode == 'init':
        dpid_offset_list = dpid_offset_range(len(worker_ip_list))
        offset_idx = 0

    processes = []
    result_queue = multiprocessing.Queue()

    for worker_ip, worker_port in zip(worker_ip_list, worker_port_list):
        if opcode == 'init':
            data['dpid_offset'] = dpid_offset_list[offset_idx]
            offset_idx += 1

        if is_serial:
            # We do not want to have parallel jobs in case of start.
            # We want serialization
            logging.info('[{0}] is running in serial mode'.format(opcode))
            processes.append(
                make_post_request_runner(worker_ip, worker_port, opcode, data,
                                         result_queue))
        else:
            logging.info('[{0}] is running in parallel mode'.format(opcode))
            process = multiprocessing.Process(target=make_post_request_runner,
                                              args=(worker_ip,
                                                    worker_port,
                                                    opcode,
                                                    data,
                                                    result_queue,))
            processes.append(process)
            process.start()

    for process in processes:
        if type(process) != type(0):
            process.join()

    return [result_queue.get() for _ in processes]


def aggregate_broadcast_response(responses):
    """Perform an aggregation on a list of HTTP responses
    If all the responses status code is successful return 200 else return 500
    Gather all the responses text in a list

    Args:
      responses (list): A list of HTTP responses

    Returns:
      status (int): The aggregate status code
      body (list): The list of all the responses text
    """
    status = 200 if all(
        r.status_code >= 200 and r.status_code < 300 for r in responses) else 500
    body = json.dumps([r.text for r in responses])
    return status, body


def master_cmd(master_ip, master_port, opcode, data=None):
    """Wrapper function to send a command to the master

    Args:
      master_ip (str): The IP address of the master
      master_port (int): The port of the master
      opcode (str): The REST API endpoint (the command we want to send)

    Returns:
      requests.models.Response: The HTTP response for the performed request
    """
    return make_post_request(master_ip, master_port, opcode, data)
