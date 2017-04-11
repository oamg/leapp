#!/usr/bin/sh
pushd integration-tests/vmdefs/centos6-guest-httpd/
sudo vagrant up
popd
pushd integration-tests/vmdefs/centos7-target/
sudo vagrant up
popd
