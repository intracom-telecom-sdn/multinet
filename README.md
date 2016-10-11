[![Code Climate](https://codeclimate.com/github/intracom-telecom-sdn/multinet/badges/gpa.svg)](https://codeclimate.com/github/intracom-telecom-sdn/multinet)
[![Code Health](https://landscape.io/github/intracom-telecom-sdn/multinet/master/landscape.svg?style=flat)](https://landscape.io/github/intracom-telecom-sdn/multinet/master)
[![Build Status](https://travis-ci.org/intracom-telecom-sdn/multinet.svg?branch=squash_commits)](https://travis-ci.org/intracom-telecom-sdn/multinet)
[![Docker Automated build](https://img.shields.io/docker/automated/jrottenberg/ffmpeg.svg?maxAge=2592000)](https://hub.docker.com/r/intracom/multinet/)

# Multinet

The goal of Multinet is to provide a fast, controlled and resource-efficient way
to boot large-scale SDN topologies. It builds on the [Mininet](https://github.com/mininet/mininet)
project to emulate SDN networks via multiple isolated topologies, each launched on
a separate machine, and all connected to the same controller.

Multinet has been verified with the Lithium release of the OpenDaylight controller,
where we managed to boot and connect a topology of 3000+ OVS OF 1.3 switches to a
single controller instance in less than 10 minutes. The controller was running on a
moderate-sized VM (8 VCPUs, 32GB memory) and the multinet topology over 10 small-sized
VMs (1 VCPU, 4GB memory each).


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

- Software dependencies:
    - Python 2.7
    - `bottle`, `requests` and `paramiko` Python packages
    - a recent version of Mininet (we support 2.2.1rc)
    - [Mausezahn](http://www.perihel.at/sec/mz/), tool for network traffic generation.
- Connectivity:
    - the machines should be able to communicate with each other
    - the machines should have SSH connectivity

In the next section we demonstrate how to prepare such an environment using
[Vagrant](https://www.vagrantup.com/) to provision and boot multiple VMs.
If you already have a custom environment set up, jump to
[configuration](#configuration) section.


#### Environment setup using Vagrant

You can use Vagrant to setup a testing environment quickly.
Using the provided `Vagrantfile` you can boot a configurable number of
fully provisioned VMs in a private network and specify their IP scheme.

Under the `deploy/vagrant` directory we provide scripts and Vagrantfiles to
automatically setup a distributed environment of VMs to run Multinet. The steps
for this are:

1. Provision the base box from which VMs will be instantiated:

   ```bash
   [user@machine multinet/]$ cd deploy/vagrant/base/
   ```

   If you sit behind a proxy, edit the `http_proxy` variable in the
   `Vagrantfile`. Then start provisioning:

   ```bash
   [user@machine multinet/deploy/vagrant/base]$ vagrant up
   ```

   When the above command finishes, package the base box that has been created:

   ```bash
   [user@machine multinet/deploy/vagrant/base]$ vagrant package --output mh-provisioned.box
   [user@machine multinet/deploy/vagrant/base]$ vagrant box add mh-provisioned mh-provisioned.box
   [user@machine multinet/deploy/vagrant/base]$ vagrant destroy
   ```

   For more info on Vagrant box packaging take a look at
   [this guide](https://scotch.io/tutorials/how-to-create-a-vagrant-base-box-from-an-existing-one)

2. Configure the VMs:

   ```bash
   [user@machine multinet/]$ cd deploy/vagrant/packaged_multi/
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
     [user@machine multinet/deploy/vagrant/packaged_multi]$ vagrant up
     ```

You should now have a number of interconnected VMs with all the dependencies installed.

#### Environment setup using Docker

In order to create a docker container we must first create an image which will
be used as a base for creating one or more docker containers. For the creation
of a docker image we provide a dockerfile

1. Install docker: [docker installation guides](https://docs.docker.com/engine/installation/)

2. Creation of docker image (without proxy settings):

   ```bash
   [user@machine multinet/]$ cd deploy/docker/no_proxy/
   [user@machine multinet/deploy/docker/no_proxy/]$ sudo docker build -t multinet_image .
   ```

After this step when you run the command

   ```bash
   [user@machine multinet/deploy/docker/no_proxy/]$ sudo docker images
   ```

You should see something like the following output

   ```bash
   REPOSITORY          TAG                   IMAGE ID            CREATED             SIZE
   <repo_name>         multinet_image        a75c906f03c7        1 minute ago        1.72 GB
   ```

3. Create containers from the created image: Open 2 terminals and execute the
following command in order to create 2 docker containers

   ```bash
   [user@machine]$ sudo docker run -it <repo_name>:multinet_image /bin/bash
   ```

After running the above commands on each terminal you should see the command
prompt of the container. It should be something like the following

   ```bash
   root@cfb6dccfc41d:/#
   ```

The 2 containers are interconnected you can get the ip address information if
you run the command

   ```bash
   root@cfb6dccfc41d:/# ifconfig
   ```

The default docker network for the containers is 172.17.0.0/16. Use the IP
addresses you of docker containers in the configuration file for the
`"master_ip":` and `"worker_ip_list":`, see next in the document in the
`configuration` section of multinet. For more information about docker
container networks visit the link
[Understand Docker container networks](https://docker.github.io/engine/userguide/networking/)



#### Configuration

To start using Multinet, the first step is to clone the Multinet repository on your
local machine. This machine is supposed to act as the __client machine__ to Multinet, and is
denoted in the following examples with the `[user@machine]` prompt.

Once you have the repository checked out, you may proceed with some configuration.

_Deployment configuration_

Edit the configuration file to your IP sceme:

  ```bash
  [user@machine multinet/]$ vim config/config.json
  ```

  ```json
  {
    "master_ip" : "10.1.1.80",
    "master_port": 3300,
    "worker_ip_list": ["10.1.1.80", "10.1.1.81"],
    "worker_port": 3333,

    "deploy": {
      "multinet_base_dir": "/home/vagrant/multinet",
      "ssh_port": 22,
      "username": "vagrant",
      "password": "vagrant"
    }
  }
  ```
- `master_ip` is the IP address of the machine where the master will run
- `master_port` is the port where the master listens for REST requests
  from the user or any external client application
- `worker_ip_list` is the list with the IPs of all machines where workers
  will be created to launch topologies
- `worker_port` is the port where each worker listens for REST requests
  from the master
- `multinet_base_dir` is the location where the Multinet repo was cloned on the
  client machine
- `ssh_port` is the port where the master and worker machines listen for SSH connections
- `username`, `password` are the credentials used to access via SSH the master and
  worker machines

_Topology configuration_

Edit the configuration file to the desired topology features:

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
      "hosts_per_switch":2,
      "traffic_generation_duration_ms":60000,
      "interpacket_delay_ms":5000
    }
  }
  ```

- `controller_ip_address` is the IP address of the machine where the
   SDN controller will run
- `controller_of_port` is the port where the controller listens for
   OpenFlow messages
- `switch_type` is the type of soft switch used for the emulation
   (supported types: `ovsk` for OVS OF1.3 switches, `user` for CPqD OF1.3 switches)
- `topo_type` is the type of topologies to be booted on every worker
   node (out of the box supported types: `linear`, `mesh`, `ring`, `disconnected`)
- `topo_size` is the size of topologies to be booted on every worker node
- `group_size`, `group_delay` are the parameters defining the gradual
   bootup groups (see section below)
- `hosts_per_switch` is the number of hosts connected to each switch of
   the topology
- `traffic_generation_duration_ms` is the amount of time in milliseconds, during
   which `PACKET_IN`'s with ARP payload, will be transmitted.
- `interpacket_delay_ms` is connected to the `traffic_generation_duration_ms`
   and is the interval between consecutive `PACKET_IN`'s, with ARP
   payload, sent from a particular Multinet worker.



#### Deployment

The goal of this phase is to deploy the Multinet master and worker nodes on a set of
up and running physical or virtual machines that satisfy the conditions mentioned above.
The provided `deploy` script automates the process of copying the required files on
each machine and starting the `master` and `worker` REST servers.

Run the `deploy` script from the client machine to copy the
necessary files and start the master and the workers:

   ```bash
   [user@machine multinet/]$ bin/deploy --json-config config/config.json
   ```

#### Initialize Multinet topology

This step initializes the distributed topologies _without connecting them to
the controller_. It creates every necessary component of the topology, such
as switches, links, hosts, etc.

Run the following command from the client machine:

   ```bash
   [user@machine multinet]$ bin/handlers/init_topos --json-config config/config.json
   ```

The above will send an `init` command to every worker node concurrently,
and an identical Mininet topology will be booted on every worker machine.
If _all_ topologies are initialized successfully you should get a `200 OK`
output message on the client machine. If any topology fails to initialize
successfully, an error message will be printed.


#### Start Multinet topology

In this step the initialized topologies are being connected to the SDN controller.
Multinet provides control over the way that the topologies are being
connected to the controller, allowing gradual connection in a group-wise
fashion. The rationale behind this is to prevent the controller from being
overwhelmed at cases where a large number of switches are being exposed to it at once.
As a result, the gradual start up enables investigating different policies of
connecting large-scale topologies to the controller.

The `group_size` and `group_delay` configuration options control the way that the
distributed topologies are being connected to the controller. The connection
process proceeds in intervals as follows: at every step, `group_size`
switches from _every_ worker node will be connected to the controller, and
after that, a delay of `group_delay` milliseconds will follow before
proceeding to the next interval. Note that each worker node will execute the
gradual booting process independent from the others, without employing any
kind of intermediate synchronization.

To connect a Multinet topology after it has been initialized, run the following
command from the client machine:

   ```bash
   [user@machine multinet/]$ bin/handlers/start_topos --json-config config/config.json
   ```

The above will send a `start` command to every worker node in parallel and
initiate the gradual connections of the topologies.
If _all_ topologies are connected successfully you should get a `200 OK`
output message on the client machine. If any topology fails to connect,
an error message will be printed.


#### Interact with Multinet topology

##### Get the number of switches

To query Multinet for the number of booted switches on each worker node, run the
following command from the client machine:

   ```bash
   [user@machine multinet/]$ bin/handlers/get_switches --json-config config/config.json
   ```

If the distributed topologies have been successfully booted, you should
get a `200 OK` message and the number of switches booted on each worker node.


##### Get the number of installed flows on switches of the topology

To query Multinet for the number of all installed flows on topology switches on
each worker, we can use the following command:

   ```bash
   [user@machine multinet/]$ bin/handlers/get_flows --json-config config/config.json
   ```

With this command on each switch we get a dump of its flows and we count them.
For each worker we add the different counts of switches flows and we get the
total installed flows for all the switches on the worker node. We return the
per Multinet worker total installed flows.


##### Do a pingall operation

To perform a "pingall" operation on every worker node in parallel run the following
command from the client machine:

   ```bash
   [user@machine multinet/]$ bin/handlers/pingall --json-config config/config.json
   ```

If the operation runs on a successfully booted topology you should
synchronously get a `200 OK` response code and the pingall output should
be logged.  _Note_ that a `pingall` operation may take a long time to complete if the
topology has many hosts.


##### Trigger host visibility

When connecting a Multinet topology to the OpenDaylight controller,
the hosts are not made automatically visible by the L2 switch plugin,
but rather when they generate traffic.
To trigger host visibility, we have opted to perform a dummy ping from each
host to the controller, which fires a `PACKET_IN` transmission.

To do this, run the following command from the client machine:

   ```bash
   [user@machine multinet/]$ bin/handlers/detect_hosts --json-config config/config.json
   ```

If all the topologies are booted successfully you should synchronously
get a `200 OK` response code.  _Note_ that a `detect_hosts` operation may take a long
time to complete if the topology has many hosts.



#### Stop Multinet topology

To stop a Multinet topology run the following command from the client machine:

   ```bash
   [user@machine multinet/]$ bin/handlers/stop_topos --json-config config/config.json
   ```

The above will send a `stop` command to every worker node in parallel and destroy the
topologies. If all the topologies are destroyed successfully, you should synchronously
get a `200 OK` output message.


#### Clean machines from Multinet installation

A dedicated script exist to revert the Multinet deployment. To clean all the Multinet
machines simply run:

```bash
[user@machine multinet/]$ bin/cleanup --json-config config.json
```


#### Generate PACKET_IN events with ARP payload

Multinet has the capability to generate traffic from switches to the controller.
This traffic consists of `PACKET_IN` events, which contain in their `Data` field,
ARP payload. This operation requires to have defined 2, as a minimum value of
`hosts_per_switch`, in the `topo` section of the configuration file.
 For more information see in the **Configuration** section above.

If we asume the case that we use OpenDaylight controller with a proper
configuration, to connect our multinet topology, the above mentioned
`PACKET_IN` traffic will have as a result the provoke of `FLOW_MOD`'s,
transmitted from the controller to the switches. Controller must have the
following plugins installed:

- `odl-restconf-all`
- `odl-openflowplugin-flow-services`
- `odl-l2switch-switch`

Aditionally we must change the values of the following configuration keys in
the mentioned XML configuration files of the controller:

- `<controller root directory>/etc/opendaylight/karaf/54-arphandler.xml`
  - Inside the above mentioned file there is a configuration option, the
    `is-proactive-flood-mode`. We must set its value to `false`:
    ```xml
       <is-proactive-flood-mode>false</is-proactive-flood-mode>
    ```
- `<controller root directory>/etc/opendaylight/karaf/58-l2switchmain.xml`
  - inside the above mentioned file we have two configuration options, the
    `reactive-flow-idle-timeout` and `reactive-flow-hard-timeout`. We must set
    the minimum value for these configuration keys, which is equal to 1:
    ```xml
       <reactive-flow-idle-timeout>1</reactive-flow-idle-timeout>
       <reactive-flow-hard-timeout>1</reactive-flow-hard-timeout>
    ```

If the XML configuration files do not exist, we must start and stop the
controller once to provoke the generation of these files.

The operational result of the above configuration is presented in the
following diagram:

![PacketIN_generation_diagram](figs/multinet_traffic_gen.png)

In order to use the `PACKET_IN` generation capability, the following command must
be executed:

```bash
[user@machine multinet/]$ bin/handlers/traffic_gen --json-config config/config.json
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
from the client machine. At the same time, it orchestrates the pool of workers.
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
| `.travis.yml`       | Travis CI job |
| `bin/`              | Binaries |
| `bin/handlers/`     | Command Line Handlers |
| `bin/cleanuph`      | Cleanup script to reset the Multinet machines environment |
| `bin/deploy`        | Automation script to copy and start the master and the workers in the Multinet machines |
| `config/`           | Configuration file for the handlers, the deployment and the master |
| `figs/`             | Figures needed for documentation |
| `multi/`            | Module containing the Master / Worker REST servers |
| `net/`              | Module containing the Mininet related functionality |
| `net/multinet.py`   | Class inheriting from the core `Mininet` with added / modified functionality |
| `net/topologies.py` | example topologies |
| `test`              | basic functionality tests |
| `travis-jobs`       | Travis CI machine provisioning helper scripts |
| `util/`             | Utility modules |
| `vagrant/`          | Vagrantfiles for fast provisioning of a running environment |


#### Interacting with the master programmatically

##### Via REST

To make easier the communication between a client application and the master node, we augmented it
with a REST API. The client application can issue the POST requests shown below to interact with
Multinet programmatically. In essence, the command line handlers presented in the previous sections are
wrapper scripts to those POST requests.

- Initialize Multinet topology
  ```python
  @bottle.route('/init', method='POST')
  ```
  When making a POST request to the `init` endpoint, you must also send a JSON
  body with the following format (also see the
  [Initialize Multinet topology](#initialize-multinet-topology) section)
  ```json
  {
        "controller_ip_address":"10.1.1.39",
        "controller_of_port":6653,
        "switch_type":"ovsk",
        "topo_type":"linear",
        "topo_size":30,
        "group_size":3,
        "group_delay":100,
        "hosts_per_switch":2,
        "traffic_generation_duration_ms":60000,
        "interpacket_delay_ms":5000
  }
  ```

- Start Multinet topology
  ```python
  @bottle.route('/start', method='POST')
  ```

- Get the number of switches
  ```python
  @bottle.route('/get_switches', method='POST')
  ```

- Perform a `pingall` in each topology
  ```python
  @bottle.route('/ping_all', method='POST')
  ```

- Make the hosts visible
  ```python
  @bottle.route('/detect_hosts', method='POST')
  ```

- Stop the topologies
  ```python
  @bottle.route('/stop', method='POST')
  ```

- Generate `PACKET_IN` traffic
  ```python
  @bottle.route('/generate_traffic', method='POST')
  ```


##### Via Python

You can also utilize the wrappers from the `multinet_requests` module for the
same purpose. Example:

1. For initialization
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
       "hosts_per_switch":2,
       "traffic_generation_duration_ms":60000,
       "interpacket_delay_ms":5000
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

To be able to plug any topology created with the high level Mininet API to Multinet,
modify the build method to conform with the following method signature:
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

2. Add the new topology to the `Multinet.TOPOS` dictionary

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
