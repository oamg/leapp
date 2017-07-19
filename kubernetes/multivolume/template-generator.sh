#!/bin/sh
readonly LEAPP_MACRO_FOLDER=/var/lib/leapp/macrocontainers
PARAM_CONTAINER_NAME=""
PARAM_PORTS=()
PARAM_TAR_IMG_URL=""
PARAM_SVC_ONLY=""
PARAM_POD_ONLY=""

function error() {
    local MSG="ERROR: Unknown error"

    if [[ ! -z $1 ]]; then
        MSG="ERROR: $1"
    fi
    echo $MSG

    exit -1
}

function warning() {
    if [[ -z $1 ]]; then
        return
    fi
    echo "WARNING: $1"
}

function usage() {
    echo "$(basename $0) OPTIONS"
    echo "  -c/--container-name  - container name"
    echo "  -h/--help            - prints this help"
    echo "  -i/--image-url       - URI to tared image"
    echo "  -p/--pod             - generate only pod template"
    echo "  -s/--service         - generate only service tempate"
    echo "  -t/--tcp-port        - exported tcp port in form" 
    echo "                         [<exposed-port>:]<container-port>"
    echo "                         can be used multiple times"
}

function sanitize_container_name() {
    echo $1 | sed -e 's/_/-/g'
}

function parse_params() {
    #global PARAM_*

    local PORTS

    while [[ $# -ge 1 ]]; do
        case $1 in
            -c|--container-name)
                shift
                PARAM_CONTAINER_NAME=$1
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            -i|--image-url)
                shift
                PARAM_TAR_IMG_URL=$1
                ;;
            -p|--pod)
                PARAM_POD_ONLY="1"
                ;;
            -s|--service)
                PARAM_SVC_ONLY="1"
                ;;
            -t|--tcp-port)
                shift
                local PORT=$1

                echo $PORT | grep -e "^\(\([0-9]\+\):\)\?[0-9]\+$" > /dev/null 2>&1 || error "Invalid port definition \"$PORT\", expected format is: <target-port>:<source-port>"
                echo $PORT | grep -e "^[0-9]\+$" > /dev/null 2>&1 && PORT=$PORT:$PORT

                IFS=':' read -r -a PORTS <<< "$PORT"

                #if [[ ${PORTS[0]} .... ]]

                PARAM_PORTS+=$PORT
                ;;
            *)
                usage
                error "Unknown argument: \"$1\"" 
                ;;
        esac
        shift
    done
    
    if [[ ! -z $PARAM_SVC_ONLY ]] && [[ ! -z $PARAM_POD_ONLY ]]; then
        error "-s and -p cannot be used together"  
    elif [[ -z $PARAM_CONTAINER_NAME ]]; then
        error "Please provide a container name"
    elif [[ -z $PARAM_TAR_IMG_URL ]]; then
        error "Please provide a url where the tar image is available"
    fi
}

function generate_pod_file() {
    #global PARAM_PORTS
    #global PARAM_TAR_IMG_URL

    local CONTAINER_NAME=$1
    local SANIT_CONTAINER_NAME=$(sanitize_container_name $CONTAINER_NAME)
    local PORTS=$(generate_ports_list $PARAM_PORTS)
    local OS_VERSION=$(get_system_version $CONTAINER_NAME) 
    local CGROUPS_MOUNT
    local CGROUPS_VOLUME

    if [[ "$OS_VERSION" != "6" ]]; then
        CGROUPS_MOUNT=$(
            echo "    - name: ${SANIT_CONTAINER_NAME}-cgroup"
            echo "      mountPath: /sys/fs/cgroup"
            echo "      readOnly: true"
            echo "    - name: ${SANIT_CONTAINER_NAME}-tmp"
            echo "      mountPath: /tmp"
            echo "    - name: ${SANIT_CONTAINER_NAME}-run"
            echo "      mountPath: /run"
        )
        CGROUPS_VOLUME=$(
            echo "  - name: ${SANIT_CONTAINER_NAME}-cgroup"
            echo "    hostPath:"
            echo "      path: /sys/fs/cgroup"
            echo "  - name: ${SANIT_CONTAINER_NAME}-tmp"
            echo "    emptyDir:"
            echo "      medium: \"Memory\""
            echo "  - name: ${SANIT_CONTAINER_NAME}-run"
            echo "    emptyDir:"
            echo "      medium: \"Memory\""
        )
    fi

    cat > $CONTAINER_NAME-pod.yaml << EOF
apiVersion: v1
kind: Pod
metadata:
  name: leapp-${SANIT_CONTAINER_NAME}-pod
  labels:
    name: leapp-${SANIT_CONTAINER_NAME}-label
  annotations:
    pod.beta.kubernetes.io/init-containers: '[
        {
            "name": "${SANIT_CONTAINER_NAME}-init",
            "image": "busybox",
            "command": ["sh", "-c", "mkdir -p /work-dir && wget -O /work-dir/image.tar $PARAM_TAR_IMG_URL && cd /work-dir && tar -xf image.tar && mkdir -p /work-dir/var/log/journal/\$(cat /work-dir/etc/machine-id)"],
            "volumeMounts": [
$(generate_init_pv_mounts $CONTAINER_NAME /work-dir)
            ]
        }
    ]'
spec:
  containers:
  - name: $SANIT_CONTAINER_NAME
    image: gazdown/leapp-scratch:$OS_VERSION
$([[ ! -z $PORTS ]] && echo "    ports:")
${PORTS}
    
    volumeMounts:
${CGROUPS_MOUNT}
$(generate_pv_mounts $CONTAINER_NAME)
  volumes:
${CGROUPS_VOLUME}
$(generate_pv_list $CONTAINER_NAME)
EOF
}

function generate_ports_list() {
    local PORTS
    for port in $1; do
        IFS=':' read -r -a PORTS <<< "$port"
        echo "    - containerPort: ${PORTS[1]}"
    done
}

function get_system_version() {
    local CONTAINER_NAME=$1
    local VERSION=6   ## DEFAULT is set to 6, because 6 is completely empty image

    grep -e "6\.[0-9]\+" $LEAPP_MACRO_FOLDER/$CONTAINER_NAME/etc/redhat-release > /dev/null 2>&1 && VERSION=6 
    grep -e "7\.[0-9]\+" $LEAPP_MACRO_FOLDER/$CONTAINER_NAME/etc/redhat-release > /dev/null 2>&1 && VERSION=7
        
    echo $VERSION
}

function generate_pv_list() {
    local CONTAINER_NAME=$1
    local SANIT_CONTAINER_NAME=$(sanitize_container_name $CONTAINER_NAME)

    for path in $(find $LEAPP_MACRO_FOLDER/$CONTAINER_NAME -mindepth 1 -maxdepth 1 -not -empty -type d); do
        folder=$(basename $path)
        echo "  - name: $SANIT_CONTAINER_NAME-$folder-vol"
        echo "    emptyDir: {}"
    done
}

function generate_init_pv_mounts() {
    local CONTAINER_NAME=$1
    local PREFIX=$2
    local SANIT_CONTAINER_NAME=$(sanitize_container_name $CONTAINER_NAME)
    local FIRST_LINE="1"

    for path in $(find $LEAPP_MACRO_FOLDER/$CONTAINER_NAME -mindepth 1 -maxdepth 1 -not -empty -type d); do
        folder=$(basename $path)
        if [[ ! -z $FIRST_LINE ]]; then
            unset FIRST_LINE
        else
            echo "                ,"
        fi

        echo "                {"
        echo "                  \"name\": \"$SANIT_CONTAINER_NAME-$folder-vol\"",
        echo "                  \"mountPath\": \"$PREFIX/$folder\""
        echo "                }"
    done
}

function generate_pv_mounts() {
    local CONTAINER_NAME=$1
    local PREFIX=$2
    local SANIT_CONTAINER_NAME=$(sanitize_container_name $CONTAINER_NAME)

    for path in $(find $LEAPP_MACRO_FOLDER/$CONTAINER_NAME -mindepth 1 -maxdepth 1 -not -empty -type d); do
        folder=$(basename $path)
        echo "    - name: $SANIT_CONTAINER_NAME-$folder-vol"
        echo "      mountPath: $PREFIX/$folder"
    done
}

function generate_service_file() {
    local CONTAINER_NAME=$1
    local SANIT_CONTAINER_NAME=$(sanitize_container_name $CONTAINER_NAME)
    local PORTS=$(generate_svc_ports $2 $SANIT_CONTAINER_NAME)

    cat > $CONTAINER_NAME-service.yaml << EOF
apiVersion: v1
kind: Service
metadata:
  name: leapp-${SANIT_CONTAINER_NAME}-service 
  labels:
    name: leapp-${SANIT_CONTAINER_NAME}-label
spec:
$([[ ! -z $PORTS ]] && echo "  ports:")
${PORTS}
  selector:
    name: leapp-${SANIT_CONTAINER_NAME}-label
EOF
}


function generate_svc_ports() {
    local PORTS

    for port in $1; do
        IFS=':' read -r -a PORTS <<< "$port"
        echo "  - port: ${PORTS[0]}"
        echo "    targetPort: ${PORTS[1]}"
        echo "    protocol: TCP"
        echo "    name: leapp-$2-${PORTS[0]}-${PORTS[1]}-port"
    done
}

function main() {
    parse_params $@
    
    if [[ -z $PARAM_SVC_ONLY ]]; then
        generate_pod_file $PARAM_CONTAINER_NAME

        curl --fail --head $PARAM_TAR_IMG_URL > /dev/null 2>&1
        [ $? -eq 0 ] || warning "File $PARAM_TAR_IMG_URL is not accessible"
    fi
        
    [ -z $PARAM_POD_ONLY ] && generate_service_file $PARAM_CONTAINER_NAME $PARAM_PORTS
}

main $@
