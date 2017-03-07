#!/usr/bin/sh

# Start the source application
pushd ansible/rhel6-guest-lamp
sudo vagrant up
popd

# Start the target container host VM
pushd ansible/rhel7-target
sudo vagrant up
popd
