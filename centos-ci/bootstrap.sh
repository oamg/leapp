#!/bin/bash

set -e

if [[ $(id -u) != 0 ]]; then
   echo "$0 needs to be run as root" ; exit 1
fi

pip install ansible==2.2.0

ansible-playbook ansible/playbook.yml

cd /srv/le-app && scl enable rh-python35 "pipenv shell 'behave'"
