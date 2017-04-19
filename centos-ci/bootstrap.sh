#!/bin/bash

set -ex

if [[ $(id -u) != 0 ]]; then
   echo "$0 needs to be run as root" ; exit 1
fi

yum install -y http://dl.fedoraproject.org/pub/epel/7/x86_64/e/epel-release-7-9.noarch.rpm
yum install -y python2-pip gcc redhat-rpm-config openssl-devel python-devel

pip install ansible==2.2.0

cd centos-ci/ansible/

ansible-playbook -i 'localhost,' -c local playbook.yml

scl enable rh-python35 sclo-vagrant1 -- sh -xc "cd ../.. && pipenv shell 'cd integration-tests && behave ; exit \\\$?'"
