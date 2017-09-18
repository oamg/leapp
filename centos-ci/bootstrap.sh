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

yum install -y http://dl.fedoraproject.org/pub/epel/7/x86_64/e/epel-release-7-10.noarch.rpm
yum install -y python2-pip gcc redhat-rpm-config openssl-devel python-devel wget git ansible

# Interim EPEL-based approach to enable testing of --ask-pass option
yum install -y sshpass
time_since_begining "step1: install yum deps"

yum install -y yum-utils wget

pushd /tmp
wget https://copr-be.cloud.fedoraproject.org/results/evilissimo/leapp/pubkey.gpg
rpm --import /tmp/pubkey.gpg
popd

yum-config-manager --add-repo https://copr-be.cloud.fedoraproject.org/results/evilissimo/leapp/epel-7-x86_64/

# Check the RPM can be built & installed successfully
yum install -y tito python2-nmap

pushd /tmp/
git clone https://github.com/leapp-to/snactor snactor-build
cd snactor-build
yum-builddep python-snactor.spec -y
TERM=xterm tito build --rpm --test --install || (echo "Failed to build and install snactor" && exit 1)
popd

yum-builddep -y leapp.spec
TERM=xterm tito build --rpm --test || (echo "Failed to build LeApp" && exit 1)
yum install -y /tmp/tito/noarch/leapp-tool-*.noarch.rpm /tmp/tito/noarch/python2-leapp-*.noarch.rpm /tmp/tito/noarch/leapp-cockpit-*.noarch.rpm /tmp/tito/x86_64/leapp-actor-tools-*.x86_64.rpm

time_since_begining "step2: build and install RPM"

# Configure the system to run the integration tests

echo "$(print_date): running ansible playbook"
cd centos-ci/ansible/
time ansible-playbook -i 'localhost,' -c local playbook.yml
time_since_begining "step3: run ansible roles scl, vagrant, cockpit-integration"

echo "$(print_date): running basic remote authentication tests with pipsi"
time scl enable rh-python35 sclo-vagrant1 -- sh -xc \
    'export LEAPP_TEST_KEEP_VMS=1; cd ../../integration-tests && behave --no-color --junit -i remote-authentication; exit \$?'
time_since_begining "step4: run basic remote authentication tests with pipsi"


echo "$(print_date): running full integration tests with installed RPM"
Xvfb :19 -screen 0 1024x768x16 &
export DISPLAY=:19
time scl enable rh-python35 sclo-vagrant1 -- sh -xc \
    'export LEAPP_TEST_RPM=1; cd ../../integration-tests && behave --no-color --junit; exit \$?'
time_since_begining "step5: run full integration tests with installed RPM"
