#!/usr/bin/sh

# Start the source application
pushd demo/vmdefs/centos6-guest
sudo vagrant up
popd

# Start the target container host VM
pushd demo/vmdefs/centos7-target
sudo vagrant up
popd
