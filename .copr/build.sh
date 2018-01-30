#!/bin/bash

BRANCH=master
LEAPP_PATCHES_SINCE_RELEASE="$(git log `git describe  --abbrev=0`..HEAD --format=oneline | wc -l)"


rm -rf leapp-build
mkdir -p leapp-build
pushd leapp-build

git clone --depth=1000 https://github.com/leapp-to/leapp-actors
    pushd leapp-actors
    LEAPP_ACTORS_PATCHES_SINCE_RELEASE="$(git log `git describe  --abbrev=0`..HEAD --format=oneline | wc -l)"
    rm -rf .git
    popd

git clone --depth=1000 https://github.com/leapp-to/leappctl
    pushd leappctl
    LEAPPCTL_PATCHES_SINCE_RELEASE="$(git log `git describe  --abbrev=0`..HEAD --format=oneline | wc -l)"
    rm -rf .git
    popd

git clone --depth=1000 https://github.com/leapp-to/snactor
    pushd snactor
    SNACTOR_PATCHES_SINCE_RELEASE="$(git log `git describe  --abbrev=0`..HEAD --format=oneline | wc -l)"
    rm -f python-snactor.spec
    rm -rf .git
    popd

git clone --depth=1000 https://github.com/leapp-to/leapp-go
    pushd leapp-go
    LEAPP_GO_PATCHES_SINCE_RELEASE="$(git log `git describe  --abbrev=0`..HEAD --format=oneline | wc -l)"
    rm -rf .git
    popd

popd

PATCHES_SINCE_RELEASE=$(($LEAPP_ACTORS_PATCHES_SINCE_RELEASE + $LEAPPCTL_PATCHES_SINCE_RELEASE + $SNACTOR_PATCHES_SINCE_RELEASE + $LEAPP_GO_PATCHES_SINCE_RELEASE))
LEAPP_BUILD_TAG="$(date  --rfc-3339=date | tr -d '-').$PATCHES_SINCE_RELEASE"

/bin/cp ../leapp.spec .
tar czf leapp-build.tar.gz leapp-build leapp.spec

SRPMDIR="$PWD"
if [ -n "$1" ]
then
    SRPMDIR="$1"
fi

rpmbuild --define "_srcrpmdir $SRPMDIR" --define "LEAPP_BUILD_TAG $LEAPP_BUILD_TAG" -ts ./leapp-build.tar.gz

