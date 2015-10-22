#!/usr/bin/env bash

username="multinet"
password="multinet"

if [ $(id -u) -eq 0 ]; then
	egrep "^$username" /etc/passwd >/dev/null
	if [ $? -eq 0 ]; then
		echo "$username exists!"
		exit
	else
		pass=$(perl -e 'print crypt($ARGV[0], "password")' $password)
		useradd -m -p $pass $username
		[ $? -eq 0 ] && echo "User has been added to system!" || echo "Failed to add a user!"
	fi
else
	echo "Only root may add a user to the system"
	exit
fi

echo "$username  ALL=(ALL:ALL) ALL" >> /etc/sudoers