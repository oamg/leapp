#!/bin/sh

cd /opt/jboss/wildfly/bin
sudo -u jboss ./standalone.sh -b 0.0.0.0 -c standalone-full-drools.xml -Dorg.kie.demo=true -Dorg.kie.example=true
