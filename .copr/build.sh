#!/bin/bash

export
if [ -z "$(which git)" ]; then
    dnf -y install git-core
fi

if [ -n "$1" ]
then
    pushd $1
fi

BRANCH=master
LEAPP_PATCHES_SINCE_RELEASE="$(git log `git describe  --abbrev=0`..HEAD --format=oneline | wc -l)"
echo LEAPP_PATCHES_SINCE_RELEASE=$LEAPP_PATCHES_SINCE_RELEASE


rm -rf leapp-build
mkdir -p leapp-build
pushd leapp-build

git clone --depth=1000 https://github.com/leapp-to/leapp-actors
    pushd leapp-actors
    LEAPP_ACTORS_PATCHES_SINCE_RELEASE="$(git log `git describe  --abbrev=0`..HEAD --format=oneline | wc -l)"
    echo LEAPP_ACTORS_PATCHES_SINCE_RELEASE=$LEAPP_ACTORS_PATCHES_SINCE_RELEASE
    rm -rf .git
    popd

git clone --depth=1000 https://github.com/leapp-to/leappctl
    pushd leappctl
    LEAPPCTL_PATCHES_SINCE_RELEASE="$(git log `git describe  --abbrev=0`..HEAD --format=oneline | wc -l)"
    echo LEAPPCTL_PATCHES_SINCE_RELEASE=$LEAPPCTL_PATCHES_SINCE_RELEASE
    rm -rf .git
    popd

git clone --depth=1000 https://github.com/leapp-to/snactor
    pushd snactor
    SNACTOR_PATCHES_SINCE_RELEASE="$(git log `git describe  --abbrev=0`..HEAD --format=oneline | wc -l)"
    echo SNACTOR_PATCHES_SINCE_RELEASE=$SNACTOR_PATCHES_SINCE_RELEASE
    rm -f python-snactor.spec
    rm -rf .git
    popd

git clone --depth=1000 https://github.com/leapp-to/leapp-go
    pushd leapp-go
    LEAPP_GO_PATCHES_SINCE_RELEASE="$(git log `git describe  --abbrev=0`..HEAD --format=oneline | wc -l)"
    echo LEAPP_GO_PATCHES_SINCE_RELEASE=$LEAPP_GO_PATCHES_SINCE_RELEASE
    rm -rf .git
    popd

popd

VERSION=$(git describe  --abbrev=0|cut -d- -f 2)
DIST=$(git describe  --abbrev=0|cut -d- -f 3)

PATCHES_SINCE_RELEASE=$(($LEAPP_PATCHES_SINCE_RELEASE + $LEAPP_ACTORS_PATCHES_SINCE_RELEASE + $LEAPPCTL_PATCHES_SINCE_RELEASE + $SNACTOR_PATCHES_SINCE_RELEASE + $LEAPP_GO_PATCHES_SINCE_RELEASE))
echo PATCHES_SINCE_RELEASE=$PATCHES_SINCE_RELEASE
LEAPP_BUILD_TAG=".$DIST.$(date  --rfc-3339=date | tr -d '-').git.$PATCHES_SINCE_RELEASE"
echo LEAPP_BUILD_TAG=$LEAPP_BUILD_TAG

/bin/cp ../leapp.spec .
tar czf leapp-build.tar.gz leapp-build leapp.spec

SRPMDIR="$PWD"
if [ -n "$1" ]
then
    SRPMDIR="$1"
fi

rpmbuild --define "_srcrpmdir $SRPMDIR" --define "version $VERSION" --define "dist $LEAPP_BUILD_TAG" -ts ./leapp-build.tar.gz

if [ -n "$1" ]
then
    popd
fi
