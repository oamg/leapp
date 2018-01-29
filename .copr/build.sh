#!/bin/bash

BRANCH=master
PATCHES_SINCE_RELEASE="$(git log `git describe  --abbrev=0`..HEAD --format=oneline | wc -l)"

LEAPP_BUILD_TAG="$(git describe  --abbrev=0 | cut -d- -f3).$PATCHES_SINCE_RELEASE"

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

rpmbuild --define "_srcrpmdir $SRPMDIR" --define "LEAPP_BUILD_TAG $LEAPP_BUILD_TAG" -ts ./leapp-build.tar.gz

