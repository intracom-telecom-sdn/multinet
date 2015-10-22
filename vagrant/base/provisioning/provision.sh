#!/usr/bin/env bash

apt-get update
apt-get install -y build-essential git unzip wget
apt-get install -y python python-pip python-dev
pip2 install bottle
pip2 install requests
pip2 install requests --upgrade
pip2 install paramiko
git clone http://github.com/mininet/mininet $HOME/mininet
cd $HOME/mininet && git checkout -b 2.2.1
$HOME/mininet/util/install.sh -n3fv
