#!/bin/bash
export TZ=UTC
alias print_date='date --rfc-2822'
alias unixdate='date +%s'
export START_TIME=$(unixdate)

function time_since_begining() {
CURRENT_TIME=$(unixdate)
echo "########################  BUILD STEP TIME ##############################"
echo "$(( CURRENT_TIME - START_TIME)) seconds since beginning for step -  $1  "
echo "########################################################################"
}



echo "starting $0 $(print_date)"
set -ex

if [[ $(id -u) != 0 ]]; then
   echo "$0 needs to be run as root" ; exit 1
fi

yum install -y http://dl.fedoraproject.org/pub/epel/7/x86_64/e/epel-release-7-9.noarch.rpm
yum install -y python2-pip gcc redhat-rpm-config openssl-devel python-devel

# Interim EPEL-based approach to enable testing of --ask-pass option
yum install -y sshpass
time_since_begining "step1: install yum deps"


# Check the RPM can be built successfully
yum install -y tito
yum-builddep -y leapp.spec
yum install -y https://copr-be.cloud.fedoraproject.org/results/evilissimo/leapp/epel-7-x86_64/00547360-python-nmap/python2-nmap-0.6.1-1.el7.centos.noarch.rpm
TERM=xterm tito build --rpm --test || (echo "Failed to build leapp RPM" && exit 1)
yum install -y /tmp/tito/noarch/leapp-tool-*.noarch.rpm /tmp/tito/noarch/python2-leapp-*.noarch.rpm /tmp/tito/noarch/leapp-cockpit-*.noarch.rpm
# TODO: Actually use that install RPM in the integration tests

time_since_begining "step2: build and install RPM"

# Configure the system to run the integration tests
yum install -y ansible

echo "$(print_date): running ansible playbook"
cd centos-ci/ansible/
time ansible-playbook -i 'localhost,' -c local playbook.yml
time_since_begining "step3: run ansible roles scl, vagrant, cockpit-integration"

Xvfb :19 -screen 0 1024x768x16 &
export DISPLAY=:19


echo "$(print_date): running integration tests"
time scl enable rh-python35 sclo-vagrant1 -- sh -xc 'cd ../../integration-tests && behave --no-color --junit && false; exit $?'
time_since_begining "step4: run integration tests"
