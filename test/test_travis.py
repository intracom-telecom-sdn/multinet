#!/usr/bin/env python

import json
import util.multinet_requests as m_util
import os
import pytest

@pytest.fixture
def config():
    data = {}
    with open('config/test-config.json') as test_config:
        data = json.load(test_config)
    return data


def test_init(config):
    res = m_util.master_cmd(config['master_ip'],
                            config['master_port'],
                            'init',
                            config['topo'])
    assert res.status_code == 200

def test_start(config):
    res = m_util.master_cmd(config['master_ip'],
                            config['master_port'],
                            'start')
    assert res.status_code == 200

def test_get_switches(config):
    res = m_util.master_cmd(config['master_ip'],
                            config['master_port'],
                            'get_switches')
    assert res.status_code == 200
    
    dpid_range = m_util.dpid_offset_range(len(config['worker_ip_list']))
    res_json = json.loads(res.text)
    i=0
    for d in res_json:
        for k, v in json.loads(d).items():
            assert k == 'dpid-{0}'.format(dpid_range[i])
            assert int(v) == int(config['topo']['topo_size'])
            i += 1

def test_stop(config):
    res = m_util.master_cmd(config['master_ip'],
                            config['master_port'],
                            'stop')
    assert res.status_code == 200


