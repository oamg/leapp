#!/usr/bin/sh

# Start the source application
pushd ansible/centos6-guest-lamp
sudo vagrant up
popd

# Start the target container host VM
pushd ansible/centos7-target
sudo vagrant up
popd
