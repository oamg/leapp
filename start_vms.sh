#!/usr/bin/sh

# Start the source application
pushd demo/vmdefs/centos6-guest
sudo ${SRC_IP_ADDR:+SRC_IP_ADDR=${SRC_IP_ADDR}} vagrant up
popd

# Start the target container host VM
pushd demo/vmdefs/centos7-target
sudo ${DST_IP_ADDR:+DST_IP_ADDR=${DST_IP_ADDR}} vagrant up
popd
