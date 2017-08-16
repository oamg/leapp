#!/bin/sh
# Utility script to set up OpenShift along with a stateful container

ACTION=$1
CONTAINERNAME=$2
TEMPLATEDIR=${3:-"templates"} 

OCUSER=ocuser
SERVICEACCOUNT=useroot
CONTAINERPATH="/var/lib/leapp/macrocontainers/$CONTAINERNAME"
shift

function start_oc() {
    # First of all, we start the cluster
    oc cluster up

    # Create user and a project for him
    oc login -u $OCUSER
    oc new-project demo-project

    # This is only necessary for creating the Persistent Storage
    oc login -u system:admin

    # Create service account and allow to run processes as root (required for init)
    oc create serviceaccount $SERVICEACCOUNT
    oc adm policy add-scc-to-user anyuid -z $SERVICEACCOUNT

    # Change SELinux security context
    sudo chcon -R -t svirt_sandbox_file_t -l s0 $CONTAINERPATH

    # Create everything from template files
    mkdir -p $TEMPLATEDIR
    sudo python cli.py stateful --container-name $CONTAINERNAME --dest $TEMPLATEDIR --service-account $SERVICEACCOUNT --load-balancer --tcp 80 && 
    oc create -f $TEMPLATEDIR
}

function stop_oc() {
    # Switch to "system" user so we get permissions to delete storage
	oc login -u system:admin

    # Shut down the cluster
    oc delete -f $TEMPLATEDIR
	oc cluster down
}

function usage() {
    echo "Usage: $(basename $0) {start|stop} [container-name] [template-dir(default=templates/)]"
    exit 1
}

function main() {
    case $ACTION in
        start)
            if [ -z $CONTAINERNAME ]; then
                echo "container-name must be set"
                usage
            fi
            if [ ! -d $CONTAINERPATH ]; then
                echo "container-name not found"
                usage
            fi
            start_oc
            ;;
        stop)
            stop_oc
            ;;
        *)
            usage
            ;;
    esac
}

main
