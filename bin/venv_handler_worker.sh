#! /bin/bash

# Copyright (c) 2015 Intracom S.A. Telecom Solutions. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License v1.0 which accompanies this distribution,
# and is available at http://www.eclipse.org/legal/epl-v10.html

# This script is responsible for activating virtual environment for the
# worker process initialization.
# Arguments:
# 1. virtual env base path (optional argument)
# 2. PYTHONPATH
# 3. Path of the worker python file
# 4. IP address of the worker host
# 5. Port number of the REST interface of the worker process

if [ "$#" -eq 5 ]
then
    source $1/bin/activate; PYTHONPATH=$2 python $3 --rest-host $4 --rest-port $5
elif [ "$#" -eq 4 ]
then
    PYTHONPATH=$1 python $2 --rest-host $3 --rest-port $4
else
    echo "Invalid number of arguments."
    exit 1
fi