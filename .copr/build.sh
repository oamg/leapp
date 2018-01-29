#!/bin/bash

BRANCH=master

rm -rf leapp-build
mkdir -p leapp-build
pushd leapp-build
curl -L https://github.com/leapp-to/leapp-actors/archive/$BRANCH.tar.gz | tar xz
mv leapp-actors-$BRANCH leapp-actors
curl -L https://github.com/leapp-to/leappctl/archive/$BRANCH.tar.gz | tar xz
mv leappctl-$BRANCH leappctl
curl -L https://github.com/leapp-to/snactor/archive/$BRANCH.tar.gz | tar xz
mv snactor-$BRANCH snactor
rm -f snactor/python-snactor.spec
curl -L https://github.com/leapp-to/leapp-go/archive/$BRANCH.tar.gz | tar xz
mv leapp-go-$BRANCH leapp-go
popd
/bin/cp ../leapp.spec .
tar czf leapp-build.tar.gz leapp-build leapp.spec

SRPMDIR="$PWD"
if [ -n "$1" ]
then
    SRPMDIR="$1"
fi

rpmbuild --define "_srcrpmdir $SRPMDIR" -ts ./leapp-build.tar.gz

