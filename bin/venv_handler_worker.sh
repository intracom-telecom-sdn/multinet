#! /bin/bash

# Copyright (c) 2015 Intracom S.A. Telecom Solutions. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License v1.0 which accompanies this distribution,
# and is available at http://www.eclipse.org/legal/epl-v10.html

# This script is responsible for activating virtual environment for the
# worker process initialization.
# Arguments:
# 1. PYTHONPATH
# 2. Path of the worker python file
# 3. IP address of the worker host
# 4. Port number of the REST interface of the worker process

if [ "$#" -eq 4 ]
then
    source /opt/venv_multinet/bin/activate; PYTHONPATH=$1; python $2 --rest-host $3 --rest-port $4
else
    echo "Invalid number of arguments."
    exit 1
fi