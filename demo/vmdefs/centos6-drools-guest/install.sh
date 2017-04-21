#!/bin/bash

set -x

export JAVA_HOME=/usr/lib/jvm/java
export WILDFLY_VERSION=10.1.0.Final
export WILDFLY_SHA1=9ee3c0255e2e6007d502223916cefad2a1a5e333
export JBOSS_HOME=/opt/jboss/wildfly
export LAUNCH_JBOSS_IN_BACKGROUND=true
export JBOSS_BIND_ADDRESS=0.0.0.0
export KIE_REPOSITORY=https://repository.jboss.org/nexus/content/groups/public-jboss
export KIE_VERSION=6.5.0.Final
export KIE_CLASSIFIER=wildfly10
export KIE_CONTEXT_PATH=drools-wb
export KIE_SERVER_PROFILE=standalone-full
export KIE_DEMO=false
export JAVA_OPTS="-Xms256m -Xmx512m"
export KIE_DEMO=true
export KIE_SERVER_PROFILE=standalone-full-drools

yum update -y && yum -y install xmlstarlet saxon augeas bsdtar unzip java-1.8.0-openjdk-devel

groupadd -r jboss -g 2000 && useradd -u 2000 -r -g jboss -m -d /opt/jboss -s /sbin/nologin -c "JBoss user" jboss && chmod 755 /opt/jboss

cd $HOME \
 && curl -O https://download.jboss.org/wildfly/$WILDFLY_VERSION/wildfly-$WILDFLY_VERSION.tar.gz \
 && sha1sum wildfly-$WILDFLY_VERSION.tar.gz | grep $WILDFLY_SHA1 \
 && tar xf wildfly-$WILDFLY_VERSION.tar.gz \
 && mv $HOME/wildfly-$WILDFLY_VERSION $JBOSS_HOME \
 && rm wildfly-$WILDFLY_VERSION.tar.gz \
 && chown -R jboss:0 ${JBOSS_HOME} \
 && chmod -R g+rw ${JBOSS_HOME}
cd -

curl -o /opt/jboss/$KIE_CONTEXT_PATH.war $KIE_REPOSITORY/org/kie/kie-drools-wb-distribution-wars/$KIE_VERSION/kie-drools-wb-distribution-wars-$KIE_VERSION-$KIE_CLASSIFIER.war && \
unzip -q /opt/jboss/$KIE_CONTEXT_PATH.war -d $JBOSS_HOME/standalone/deployments/$KIE_CONTEXT_PATH.war &&  \
touch $JBOSS_HOME/standalone/deployments/$KIE_CONTEXT_PATH.war.dodeploy &&  \
rm -rf /opt/jboss/$KIE_CONTEXT_PATH.war

mkdir -p /opt/jboss/.m2/repository/org/guvnor/guvnor-asset-mgmt-project/$KIE_VERSION && \
curl -o /opt/jboss/.m2/repository/org/guvnor/guvnor-asset-mgmt-project/$KIE_VERSION/guvnor-asset-mgmt-project-$KIE_VERSION.jar $KIE_REPOSITORY/org/guvnor/guvnor-asset-mgmt-project/$KIE_VERSION/guvnor-asset-mgmt-project-$KIE_VERSION.jar

cp /vagrant/etc/standalone-full-drools.xml $JBOSS_HOME/standalone/configuration/standalone-full-drools.xml
cp /vagrant/etc/drools-users.properties $JBOSS_HOME/standalone/configuration/drools-users.properties
cp /vagrant/etc/drools-roles.properties $JBOSS_HOME/standalone/configuration/drools-roles.properties

chown -R jboss:jboss /opt/jboss

env > $JBOSS_HOME/install-env
