#!/usr/bin/env bash

# Copyright (c) 2015 Intracom S.A. Telecom Solutions. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License v1.0 which accompanies this distribution,
# and is available at http://www.eclipse.org/legal/epl-v10.html

apt-get -y update
git clone http://github.com/mininet/mininet $HOME/mininet
cd $HOME/mininet && git checkout -b 2.2.1
$HOME/mininet/util/install.sh -n3fv