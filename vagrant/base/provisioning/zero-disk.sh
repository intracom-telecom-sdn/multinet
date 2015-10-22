#!/usr/bin/env bash

# Zero disk space
dd if=/dev/zero of=/zero.file bs=10M count=999999999
rm /zero.file
# cat /dev/null > ~/.bash_history && history -c;exit
