#!/usr/bin/env python

import argparse
import os
from template_generator import *


LEAPP_BASEPATH = "/var/lib/leapp/macrocontainers"


def parse_params():
    def _parse_port(arg):
        docker_port, sep, container_port = arg.partition(":")
        if not container_port:
            container_port = docker_port

        return int(docker_port), int(container_port)

    def _parse_ip(arg):
        ## TODO add proper parser
        return arg

    parser = argparse.ArgumentParser(description='Generate kubernetes tempates.')
    subparser = parser.add_subparsers(dest="generator")

    multi = subparser.add_parser("multivolume", help="test")
    macro = subparser.add_parser("macroimage", help="test2")

    #selectors = []
    mandatory_groups = []

    for p in multi, macro:
        p.add_argument("--tcp", "-t", type=_parse_port, nargs="*", help="Exposed TCP ports")
        p.add_argument("--ip", "-i", type=_parse_ip, nargs="+", help="IP address on which the ports will be exposed")
        p.add_argument("--dest", "-e", default=os.getcwd(), help="Generate service template (default: true)")

        mandatory = p.add_argument_group("Mandatory arguments")
        mandatory.add_argument("--container-name", "-c", help="A name of macrocontainer", required=True)
        mandatory_groups.extend([mandatory])

        #selector = p.add_argument_group("Template selectors (optional)")
        #selector.add_argument("--pod", "-p", action="store_true", default=None, help="Generate pod template (default: true)")
        #selector.add_argument("--service", "-s", action="store_true", default=None, help="Generate service template (default: true)")
        #selectors.extend([selector])


    #multivolume specific
    mandatory_groups[0].add_argument("--image-url", "-m", help="URL to machine tar image", required=True)

    #macro specific
    #selectors[1].add_argument("--docker", "-d", action="store_true", default=None, help="Generate dockerfile (default: true)")
    macro.add_argument("--local-image", "-l", action="store_true", help="Disable pulling images on node (Default: false)", default=False)

    return parser.parse_args()


def write_file(path, content):
    f = open(path, "w")
    f.write(content)
    f.close()

def main():
    params = parse_params()

    path = "{}/{}".format(LEAPP_BASEPATH, params.container_name)

    ## Find release version
    rfile = open("{}/etc/redhat-release".format(path), "r")
    ver = re.findall(".*\srelease\s(\d+)(?:\.\d+)?.*", rfile.readline(64))
    rfile.close()

    if len(ver) and ver[0] == "6":
        system = RHEL6ContainerOS()
    elif len(ver) and ver[0] == "7":
        system = RHEL7ContainerOS()
    else:
        raise Exception("Unknown release version")

    sanit_name = TemplateGenerator.sanitize_container_name(params.container_name)
    dest = params.dest

    print("Storing templates to: {}".format(dest))

    if params.generator == "macroimage":
        #selective_templating = False

        #for i in params.pod, params.service, params.docker:
        #    if i:
        #        selective_templating = True

        template = MacroimageTemplateGenerator(
            params.container_name,
            system,
            exposed_ports = params.tcp,
            is_local = params.local_image,
            external_ips = params.ip
            )



        write_file("{}/{}-svc.yaml".format(dest, sanit_name), template.generate_service_template())
        write_file("{}/{}-pod.yaml".format(dest, sanit_name), template.generate_pod_template())
        write_file("{}/Dockerfile".format(dest, sanit_name), template.generate_dockerfile())


        print("Create a tar image of migrated machine:")
        print("  tar -czf {}/{}.tar.gz -C {} .\n".format(dest, sanit_name, path))
        print("Move it to the machine where you want to build the container \n\
along with generated Dockerfile and execute: ")
        print("  docker build -t {} .\n".format(template.macroimage_name()))

        if not params.local_image:
            print("Push the new image into registry")
            print("  docker push {}".format(template.macroimage_name()))


    elif params.generator == "multivolume":
        dirs = [ f for f in os.listdir(path)
            if os.path.isdir(os.path.join(path, f))
            and not os.path.islink(os.path.join(path, f))
            and len(os.listdir(os.path.join(path, f)))
            ]

        template = MultivolumeTemplateGenerator(
            params.container_name,
            system,
            params.image_url,
            exposed_ports = params.tcp,
            exported_paths = dirs,
            external_ips = params.ip
            )


        write_file("{}/{}-svc.yaml".format(dest, sanit_name), template.generate_service_template())
        write_file("{}/{}-pod.yaml".format(dest, sanit_name), template.generate_pod_template())

        print("Create a tar image of migrated machine:")
        print("  tar -czf {}/{}.tar.gz -C {} .\n".format(dest, os.path.basename(params.image_url), path))
        print("Move it to the web server, where it will be available under image-url you've specified ")

if __name__ == "__main__":
    main()

