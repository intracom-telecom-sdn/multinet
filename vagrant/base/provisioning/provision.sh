#!/usr/bin/env bash

sudo apt-get update
sudo apt-get install --force-yes -y build-essential git unzip wget
sudo apt-get install --force-yes -y python python-pip python-dev
sudo apt-get install --force-yes -y mz
sudo pip2 install bottle
sudo pip2 install requests
sudo pip2 install requests --upgrade
sudo pip2 install paramiko
git clone http://github.com/mininet/mininet $HOME/mininet
cd $HOME/mininet && git checkout -b 2.2.1
sudo $HOME/mininet/util/install.sh -n3fv
