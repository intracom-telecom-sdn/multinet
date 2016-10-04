#! /bin/bash

# Copyright (c) 2015 Intracom S.A. Telecom Solutions. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License v1.0 which accompanies this distribution,
# and is available at http://www.eclipse.org/legal/epl-v10.html

# This script is responsible for activating virtual environment for multinet
# handlers.
# Arguments:
# 1. virtual env base path (optional argument)
# 2. PYTHONPATH
# 3. Handler path
# 4. Config path. The json configuration file path.

if [ "$#" -eq 4 ]
then
    source $1/bin/activate; PYTHONPATH=$2 python $3 --json-config $4
elif [ "$#" -eq 3 ]
then
    PYTHONPATH=$1 python $2 --json-config $3
else
    echo "Invalid number of arguments."
    exit 1
fi