[![Code Climate](https://codeclimate.com/github/intracom-telecom-sdn/multinet/badges/gpa.svg)](https://codeclimate.com/github/intracom-telecom-sdn/multinet)
[![Code Health](https://landscape.io/github/intracom-telecom-sdn/multinet/master/landscape.svg?style=flat)](https://landscape.io/github/intracom-telecom-sdn/multinet/master)
[![Build Status](https://travis-ci.org/intracom-telecom-sdn/multinet.svg?branch=squash_commits)](https://travis-ci.org/intracom-telecom-sdn/multinet)

# Multinet

The goal of Multinet is to provide a fast, controlled and resource-efficient way
to boot large-scale SDN topologies. It builds on the [Mininet](https://github.com/mininet/mininet)
project to emulate SDN networks via multiple isolated topologies, each launched on
a separate machine, and all connected to the same controller.

Multinet has been verified with the Lithium release of the OpenDaylight controller,
where we managed to successfully boot a distributed topology of 3000 OVS switches.  


_Why isolated topologies?_

The main motivation behind Multinet was to be able to stress an SDN controller
in terms of its switch scalable limits. In this context, Multinet contents
itself to booting topologies that are isolated from each other, without really caring
to be interconnected, as we believe this policy is simple and good enough
to approximate the behavior of large-scale realistic SDN networks and their
interaction with the controller. If creating large-scale _interconnected_
topologies is your primary concern, then you might want to look at other efforts
such as [Maxinet](https://github.com/mininet/mininet/wiki/Cluster-Edition-Prototype)
or the [Cluster Edition Prototype](https://github.com/mininet/mininet/wiki/Cluster-Edition-Prototype)
of Mininet. Instead, Multinet clearly emphasizes on creating scalable pressure to
the controller and provides options to control certain aspects that affect the
switches-controller interaction, such as the way these are being connected during start-up.


_Why multiple VMs?_

The cost to boot a large Mininet topology on a single machine grows
exponentially with the number of switches. To amortize this cost, we opted to
scale out and utilize multiple VMs to spawn multiple smaller topologies in parallel.
Eventually, one of the key questions that we try to answer through Multinet is:
_what is the best time to boot-up a topology of S Mininet switches with the least
amount of resources_?

## Features

- __Large-scale SDN networks__ emulation, using multiple isolated Mininet
  topologies distributed across multiple VMs
- __Controllable boot-up__ of switches in groups of configurable size and
  configurable intermediate delay. This enables studying different policies of
  connecting large-scale topologies to the controller.
- __Centralized__ and __RESTful__ control of topologies via a master-worker architecture
- __Well-known topology types__ offered out-of-the-box (`disconnected`, `linear`,
  `ring`, `mesh`)
- __Smooth integration with custom topologies__ created via the high-level Mininet API,
  provided they have slightly modified their `build` method


![Multinet Architecture](figs/multinet.png)


## Getting Started

#### Environment setup

To use Multinet you should have a distributed environment of machines configured
as follows:

- Software dependences:
    - Python 2.7
    - `bottle`, `requests` and `paramiko` Python packages
    - a recent version of Mininet (we support 2.2.1rc)
- Connectivity:
    - the machines should be able to communicate with each other
    - the machines should have SSH connectivity

In the next section we demonstrate how to prepare such an environment using
[Vagrant](https://www.vagrantup.com/) to provision and boot multiple VMs.
If you already have a custom environment set up, jump to
[deployment](#deploy-multinet-on-the-distributed-environment) section.


#### Environment setup using Vagrant

You could also use `vagrant` to setup a testing environment quickly. 
Using the provided `Vagrantfile` you can boot a configurable number of 
fully provisioned VMs in a private network and specify their IP scheme.  
If you already have a testing environment you can skip this step.  

Under the `vagrant` directory we provide scripts and Vagrantfiles to
automatically setup a distributed environment of VMs to run Multinet. The steps
for this are:

1. Provision the base box from which VMs will be instantiated:

   ```bash
   [user@machine multinet/]$ cd vagrant/base/
   ```

   If you sit behind a proxy, edit the `http_proxy` variable in the
   `Vagrantfile`. Then start provisioning:

   ```bash
   [user@machine multinet/vagrant/base]$ vagrant up
   ```

   When the above command finishes, package the base box that has been created:

   ```bash
   [user@machine multinet/vagrant/base]$ vagrant package --output mh-provisioned.box
   [user@machine multinet/vagrant/base]$ vagrant box add mh-provisioned mh-provisioned.box
   [user@machine multinet/vagrant/base]$ vagrant destroy
   ```

   For more info on Vagrant box packaging take a look at
   [this guide](https://scotch.io/tutorials/how-to-create-a-vagrant-base-box-from-an-existing-one)

2. Configure the VMs:

   ```bash
   [user@machine multinet/]$ cd vagrant/packaged_multi/
   ```

   Edit the `Vagrantfile` according to your preferences. For example:

   ```rb
   http_proxy = ''  # if you sit behind a corporate proxy, provide it here
   mh_vm_basebox = 'mh-provisioned' # the name of the Vagrant box we created in step 2
   mh_vm_ram_mini = '2048'  # RAM size per VM
   mh_vm_cpus_mini = '2'    # number of CPUs per VM
   num_multinet_vms = 10    # total number of VMs to boot
   mh_vm_private_network_ip_mini = '10.1.1.70'  # the first IP Address in the mininet VMs IP Address range
   ```

   _Optional Configuration_
   If you need port forwarding from the master guest machine to the
   host machine, edit these variables inside the `Vagrantfile`:  

   ```rb
   forwarded_ports_master = [] # A list of the ports the guest VM needs
                               # to forward
   forwarded_ports_host = []   # The host ports where the guest ports will be
                               # forwarded to (1 - 1 correspondence)
   # Example:
   #   port 3300 from master VM will be forwarded to port 3300 of
   #   the host machine  
   #   port 6634 from master VM will be forwarded to port 6635 of
   #   the host machine  
   #   forwarded_ports_master = [3300, 6634]  
   #   forwarded_ports_host = [3300, 6635]
   ```

3. Boot the VMs:

     ```bash
     [user@machine multinet/vagrant/packaged_multi]$ vagrant up
     ```

You should now have a number of interconnected VMs with all the dependencies installed.  

#### Deploy Multinet on the distributed environment

The next phase is the deployment phase. We need to copy the `Multinet` files 
in each VM and start the `master` and the `workers`.  
We provide a `deploy` script that automates this process. To use it follow the 
following instructions

1. Clone the Multinet repository in the local machine  
2. Configure `config/config.json` with the IP scheme of your VMs:  
   ```json
   {
      "master_ip" : "10.1.1.80",
      "master_port": 3300,
      "worker_port": 3333,
      "worker_ip_list": ["10.1.1.80", "10.1.1.81"],

      "deploy": {
        "multinet_base_dir": "/home/vagrant/multinet",
        "ssh_port": 22,
        "username": "vagrant",
        "password": "vagrant"
      }
   }
   ```
   - `multinet_base_dir` is the location that the repository was cloned in the master node.
   - `master_ip` is the IP address of the machine where the master will run
   - `master_port` is the port where the master listens for REST requests
     from external client applications
   - `worker_port` is the port where each worker listens for REST requests
      from the master
   - `worker_ip_list` is the list with the IPs of all machines where workers
      will be created to launch topologies
   - `ssh_port` is the port where machines listen for SSH connections
   - `username`, `password` are the credentials used to access via SSH the machines
3. Run the `deploy` script in the external user console to copy the
   necessary files and start the master and the workers:

   ```bash
   [user@machine multinet/]$ bin/deploy --json-config config.json
   ```

#### Initialize Multinet topologies

1. Make sure the master / worker IP addresses and ports in the
   `config/config.json` file are properly configured. Then configure
   the `topo` options:

   ```json
   {
      "topo": {
        "controller_ip_address":"10.1.1.39",
        "controller_of_port":6653,
        "switch_type":"ovsk",
        "topo_type":"linear",
        "topo_size":30,
        "group_size":3,
        "group_delay":100,
        "hosts_per_switch":2
      }
   }
   ```

   Where
   - `controller_ip_address` is the IP address of the machine where the
     controller will run
   - `controller_of_port` is the port where the controller listens for
     OpenFlow traffic
   - `switch_type` is the type of soft switch used for the emulation
   - `topo_type` is the type of topology to be booted
   - `topo_size` is the size of topology to be booted
   - `group_size`, `group_delay` are the parameters defining the gradual
     bootup groups
   - `hosts_per_switch` is the number of hosts connected to each switch

2. Run the following command inside the end user machine  

   ```bash
   [user@machine multinet]$ bin/handlers/init_topos --json-config config/config.json
   ```

  This command sends an `init` command to every worker machine in parallel,
  and an identical Mininet topology will be built in each machine.  
  If all the topologies are built successfully you should synchronously
  get a `200 OK` response code.  

_Gradual Bootup_

We observed that most SDN controllers display some
instability issues when it is overwhelmed with switch additions.  
The solution we pose to this problem is the gradual switch bootup.  
In more detail, we modified the Mininet `start` method as follows
- We split the switches we need to start in groups
- The size of each group is specified by the `group_size` parameter
- We start the switches in each group normally  
- After all the switches in a group have started we insert a delay  
- The delay is specified by the `group_delay` parameter  

We have observed that this method allows us to boot larger topologies with
greater stability. Moreover it gives us a way to estimate the boot time of
a topology in a deterministic way.

#### Start Multinet topologies

Run the following command inside the end user machine  

   ```bash
   [user@machine multinet/]$ bin/handlers/start_topos --json-config <path-to-config-file>
   ```

For example:

   ```bash
   [user@machine multinet/]$ bin/handlers/start_topos --json-config config/config.json
   ```

This command should run __after__ the `init` command.  
It sends a `start` command to every worker machine in parallel and boots the
topologies.
If all the topologies are booted successfully you should synchronously
get a `200 OK` response code.  


#### Interact with the topologies

##### Make the hosts visible

When we where using the Opendaylight controller, we observed that the
hosts where not automatically visible on creation by the L2 switch plugin, 
rather they became visible when they generated traffic.  
While this is a rather logical assumption, it has its limitations when
implementing automatic lifecycle management tools for the controller stress
testing. The solution we implemented is to perform a ping from each host to
send some `PACKET_IN` openflow packets to the controller in order to detect
the hosts.  


Run the following command inside the end user machine  

   ```bash
   [user@machine multinet/]$ bin/handlers/detect_hosts --json-config <path-to-config-file>
   ```

For example:

   ```bash
   [user@machine multinet/]$ bin/handlers/detect_hosts --json-config config/config.json
   ```

This command should run __after__ the `start` command.  
It sends a `detect_hosts` command to every worker machine in parallel to make
the hosts visible in the controller side.  
If all the topologies are booted successfully you should synchronously
get a `200 OK` response code.  
_Note_ that a `detect_hosts` operation may take a long time to complete if the
topology has many hosts.

##### Get the number of switches

Run the following command inside the end user machine  

   ```bash
   [user@machine multinet/]$ bin/handlers/get_switches --json-config <path-to-config-file>
   ```

For example:

   ```bash
   [user@machine multinet/]$ bin/handlers/get_switches --json-config config/config.json
   ```

This command should run __after__ the `start` command.  
It sends a `get_switches` command to every worker machine in parallel and
queries the number of bootes switches.
If the operation runs on a successfully booted topology you should
synchronously get a `200 OK` response code and the number of switches should
be logged.  


##### Do a pingall operation

Run the following command inside the end user machine  

   ```bash
   [user@machine multinet/]$ bin/handlers/pingall --json-config <path-to-config-file>
   ```

For example:

   ```bash
   [user@machine multinet/]$ bin/handlers/pingall --json-config config/config.json
   ```

This command should run __after__ the `start` command.  
It sends a `pingall` command to every worker machine in parallel and performs
a pingall operation.
If the operation runs on a successfully booted topology you should
synchronously get a `200 OK` response code and the pingall output should
be logged.  
_Note_ that a `pingall` operation may take a long time to complete if the
topology has many hosts.  


#### Stop Multinet topologies  

Run the following command inside the end user machine:  

   ```bash
   [user@machine multinet/]$ bin/handlers/stop_topos --json-config <path-to-config-file>
   ```

For example:

   ```bash
   [user@machine multinet/]$ bin/handlers/stop_topos --json-config config/config.json
   ```

This command should run __after__ the `start` command.  
It sends a `stop` command to every worker machine in parallel and destroys the
topologies.
If all the topologies are destroyed successfully you should synchronously
get a `200 OK` response code.  


#### Clean machines from Multinet installation

A dedicated script exist to revert the Multinet deployment. To clean the VMs of Multinet simply run:  

```bash
[user@machine multinet/]$ bin/cleanup --json-config config.json
```


## System Architecture

The end goal of Multinet is to deploy a set of Mininet topologies over multiple
machines and have them connected to the same controller simultaneously. To make
this possible, every switch must have a unique DPID to avoid naming collisions
in the controller's housekeeping mechanism, and to achieve this, Multinet
automatically assigns a proper DPID offset to each Mininet topology.

The local Mininet topologies are identical in terms of size, structure and
configuration, and they are all being handled in the same fashion simultaneously.
For example, during start up, topologies are being
created simultaneously on the worker machines and populated in the same way. To
relieve the end user from having to manage each topology separately, we have
adopted a _master-worker model_ for centralized control.

The __master__ process acts as the Multinet front-end that accepts REST requests
from the end user. At the same time, it orchestrates the pool of workers.
On a user request, the master creates a separate command for each local topology
which it dispatches simultaneously to the workers.
Each __worker__ process controls a local Mininet topology. It accepts commands
from the master via REST, applies them to its topology, and responds back with
a result status. Every worker is unaware of the topologies being operated from
other workers.
The master is responsible to collect partial results and statuses from all workers
and reply to the user as soon as it has a complete global view.

For resource efficiency and speed, it is preferable to create each worker along
with its topology on a separate machine.

## Code Design

#### Code structure

| Path                                             | Description                                     |
|--------------------------------------------------|-------------------------------------------------|
| `bin/`              | Binaries |
| `bin/handlers/`     | Command Line Handlers |
| `bin/cleanup.sh`    | cleanup script to reset the virtual machines environment |
| `bin/deploy.py`     | Automation script to copy and start the master and the workers in the virtual machines |
| `config/`           | configuration file for the handlers, the deployment and the master |
| `figs/`             | Figures needed for documentation |
| `multi/`            | Module containing the Master / Worker REST servers |
| `net/`              | Module containing the Mininet related functionality |
| `net/multinet.py`   | Class inheriting from the core `Mininet` with added / modified functionality |
| `net/topologies.py` | example topologies |  
| `util/`             | Utility modules |
| `vagrant/`          | Vagrantfiles for fast provisioning of a running environment |


#### Interacting with the master programmatically

To make the communication between the user, the master and the workers easier
we designed the master (and the workers) as a REST server.
The command line handlers are essentially wrapper scripts that perform POST requests to the REST API the master exposes.  

Bellow we present a roadmap of the master API  

- Initialize the topologies  
  ```python
  @bottle.route('/init', method='POST')
  ```
  When making a POST request to the `init` endpoint, you must also send a JSON
  body with the following format (also see the 
  [Initialize Multinet topologies](#initialize-multinet-topologies) section)  
  ```json
  {
        "controller_ip_address":"10.1.1.39",
        "controller_of_port":6653,
        "switch_type":"ovsk",
        "topo_type":"linear",
        "topo_size":30,
        "group_size":3,
        "group_delay":100,
        "hosts_per_switch":2
  }
  ```

- Boot the topologies  
  ```python
  @bottle.route('/start', method='POST')
  ```

- Make the hosts visible to the controller  
  ```python
  @bottle.route('/detect_hosts', method='POST')
  ```

- Stop the topologies  
  ```python
  @bottle.route('/stop', method='POST')
  ```

- Perform a `pingall` in each topology  
  ```python
  @bottle.route('/ping_all', method='POST')
  ```

- Get the number of switches in each topology  
  ```python
  @bottle.route('/get_switches', method='POST')
  ```

You can also utilize the wrappers from the `multinet_requests` module

Example:  

1. For `init`
   ```python
   # Send a POST request to the master 'init' endpoint

   topo_data= {
       "controller_ip_address":"10.1.1.39",
       "controller_of_port":6653,
       "switch_type":"ovsk",
       "topo_type":"linear",
       "topo_size":30,
       "group_size":3,
       "group_delay":100,
       "hosts_per_switch":2
   }
   
   multinet_requests.master_cmd(master_ip,
                                master_port,
                                'init',
                                data=topo_data)
   ```

2. And for any other operation
   ```python
   # Send a POST request to any master endpoint
   # The endpoint is specified by the 'opcode' parameter
   
   opcode = choose_one_of(['start', 'get_switches', 'ping_all', 'detect_hosts', 'stop'])
   multinet_requests.master_cmd(master_ip, master_port, opcode)
   ```

#### Core components

- `Multinet` class  
  - Extends the `Mininet` class.  
  - Adds a dpid offset during the switch creation phase to distinguish between the switches in different instances.  
  - Inserts the notion of gradual switch bootup, inserting some idle time
    (`group_delay`) between the bootup of groups of switches (`group_size`)  
- `worker`  
  - creates its own `Multinet` instance  
  - creates a REST API that wraps the exposed methods of that instance.  
- `master`  
  - exposes a REST API to the end user.  
  - broadcasts the commands to the workers  
  - aggregates the responses and returns a summary response to the end user  


#### Adding your own topologies

First of all **note** that the build method signature of any existing topology
created with the high level Mininet API need to be modified to conform with
the following method signature in order to be compatible
```python
# k is the number of switches
# n is the number of hosts per switch
# dpid is the dpid offset
def build(self, k=2, n=1, dpid=1, **_opts):
```

1. Create a topology with the Mininet high level API, for example

 ```python
 ## mytopo.py
 class MyTopo(Topo):
       "Disconnected topology of k switches, with n hosts per switch."

       def build(self, k=2, n=1, dpid=1, **_opts):
           """
           k: number of switches
           n: number of hosts per switch
           dpid: the dpid offset (to enable distributed topology creation)
           """
           self.k = k
           self.n = n

           for i in xrange(k):
               # Add switch
               switch = self.addSwitch(genSwitchName(i, dpid))
               # Add hosts to switch
               for j in xrange(n):
                   host = self.addHost(genHostName(i, j, dpid, n))
                   self.addLink(host, switch)
 ```

2. Add it to the `Multinet.TOPOS` dictionary

   ```python
   # worker.py
   import mytopo ...
   Multinet.TOPOS['mytopo'] = mytopo.MyTopo
   MININET_TOPO = Multinet( ... )
   ```
   ```python
   # or from inside multinet.py
   TOPOS = {
      'linear': ...
      'mytopo': mytopo.MyTopo
   }
   ```
