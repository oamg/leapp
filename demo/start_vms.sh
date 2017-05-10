#!/usr/bin/bash
# Start all defined demo VMs
# Based on:
# http://stackoverflow.com/questions/6659689/referring-to-a-file-relative-to-executing-script
# http://stackoverflow.com/questions/2107945/how-to-loop-over-directories-in-linux

function stop_start_action(){
    case $1 in
      start)
        vagrant up
        ;;
      stop)
        vagrant stop
        ;;
      provision)
        vagrant up --provision
        ;;
      destroy)
        vagrant destroy
        ;;
      *)
        echo "invalid action $1. USAGE: $0 [ stop|start|provision|destroy]"
        exit 1
        ;;
    esac 
}


if [ $# -gt 1 ]
then
  echo "invalid argument count. USAGE: $0 [stop|start|provision|destroy"
  exit 1
elif [ $# -eq 1 ]    
then
  # after test scripts will be ammeneded this will be changed to an error
  # for now this is for backwards compatibility purpose
  action=$1
else
  action="provision"
fi

pushd "${BASH_SOURCE%/*}" || exit
for vmdef in vmdefs/*
do
  pushd ${vmdef}
    stop_start_action $action 
  popd
done
popd
