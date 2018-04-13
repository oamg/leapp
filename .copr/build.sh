#!/bin/bash
set -x

OUTDIR="$PWD"
if [ -n "$1" ]; then
    OUTDIR="$(realpath $1)"
fi

dnf -y install which

export
if [ -z "$(which git)" ]; then
    dnf -y install git-core
fi

if ! git status 2&>1 > /dev/null; then
    rm -rf leapp
    git clone https://github.com/leapp-to/leapp
    POPD=`pushd leapp`
fi

BRANCH=master
LEAPP_PATCHES_SINCE_RELEASE="$(git log `git describe  --abbrev=0`..HEAD --format=oneline | wc -l)"
echo LEAPP_PATCHES_SINCE_RELEASE=$LEAPP_PATCHES_SINCE_RELEASE

VERSION=$(git describe  --abbrev=0|cut -d- -f 2)
DIST=$(git describe  --abbrev=0|cut -d- -f 3)
LEAPP_BUILD_TAG=".$DIST.$(date  --rfc-3339=date | tr -d '-').git.$LEAPP_PATCHES_SINCE_RELEASE"

if [ -n "$POPD" ]
then
    popd
fi


echo LEAPP_BUILD_TAG=$LEAPP_BUILD_TAG
export toplevel=$(git rev-parse --show-toplevel)
git archive --remote "$toplevel" --prefix leapp-master/ HEAD > leapp-$VERSION.tar
tar --delete leapp-master/leapp.spec --file leapp-$VERSION.tar
mkdir -p leapp-master
/bin/cp ${toplevel}/leapp.spec leapp-master/leapp.spec
sed -i "s/^%global dist.*$/%global dist $LEAPP_BUILD_TAG/g" leapp-master/leapp.spec
tar --append --file leapp-$VERSION.tar leapp-master/leapp.spec

cat leapp-$VERSION.tar | gzip > leapp-$VERSION.tar.gz

echo $PWD $OUTDIR
SRPMDIR="$OUTDIR"
rpmbuild --define "_srcrpmdir $SRPMDIR" --define "version $VERSION" --define "gittag master" -ts ./leapp-$VERSION.tar.gz

