#!/usr/bin/env python

import argparse
import os
import re

from template_generator import MultivolumeTemplateGenerator
from template_generator import MacroimageTemplateGenerator
from template_generator import TemplateGenerator

from container_os import RHEL7ContainerOS
from container_os import RHEL6ContainerOS


LEAPP_BASEPATH = "/var/lib/leapp/macrocontainers"


class UnknownOSError(Exception):
    pass


def parse_params():
    def _parse_port(arg):
        docker_port, sep, container_port = arg.partition(":")
        if not container_port:
            container_port = docker_port

        return int(docker_port), int(container_port)

    def _parse_ip(arg):
        # TODO add proper parser
        return arg

    parser = argparse.ArgumentParser(description='Generate kubernetes tempates.')
    subparser = parser.add_subparsers(dest="generator")

    multi = subparser.add_parser("multivolume", help="Generate multivolume template")
    macro = subparser.add_parser("macroimage", help="Generate macroimage template")

    mandatory_groups = []

    for param in multi, macro:
        param.add_argument("--tcp", "-t", type=_parse_port, nargs="*", help="Exposed TCP ports")
        param.add_argument("--ip", "-i", type=_parse_ip, nargs="+",
                           help="IP address on which the ports will be exposed")
        param.add_argument("--dest", "-e", default=os.getcwd(), help="Generate service template (default: true)")

        mandatory = param.add_argument_group("Mandatory arguments")
        mandatory.add_argument("--container-name", "-c", help="A name of macrocontainer", required=True)
        mandatory_groups.extend([mandatory])

    # multivolume specific
    mandatory_groups[0].add_argument("--image-url", "-m", help="URL to machine tar image", required=True)

    # macro specific
    macro.add_argument("--local-image", "-l", action="store_true",
                       help="Disable pulling images on node (Default: false)",
                       default=False)

    return parser.parse_args()


def write_file(path, content):
    with open(path, "w") as f:
        f.write(content)


def offline_os_version_detection(path):
    # Find release version
    with open("{}/etc/redhat-release".format(path), "r") as rfile:
        ver = re.findall(".*\srelease\s(\d+)(?:\.\d+)?.*", rfile.readline(64))

    if len(ver) and ver[0] == "6":
        system = RHEL6ContainerOS()
    elif len(ver) and ver[0] == "7":
        system = RHEL7ContainerOS()
    else:
        raise UnknownOSError("Unknown release version")

    return system


def main():
    params = parse_params()

    path = "{}/{}".format(LEAPP_BASEPATH, params.container_name)

    sanit_name = TemplateGenerator.sanitize_container_name(params.container_name)
    dest = params.dest

    print("Storing templates to: {}".format(dest))

    if params.generator == "macroimage":
        template = MacroimageTemplateGenerator(
            params.container_name,
            offline_os_version_detection(path),
            exposed_ports=params.tcp,
            is_local=params.local_image,
            external_ips=params.ip
            )

        write_file("{}/{}-svc.yaml".format(dest, sanit_name), template.generate_service_template())
        write_file("{}/{}-pod.yaml".format(dest, sanit_name), template.generate_pod_template())
        write_file("{}/Dockerfile".format(dest, sanit_name), template.generate_dockerfile())

        print("Create a tar image of migrated machine:\n"
              "  tar -czf {dest}/{name}.tar.gz -C {path} .\n\n"
              "Move it to the machine where you want to build the container \n"
              "along with generated Dockerfile and execute: \n"
              "  docker build -t {image_name} .\n".format(dest=dest, name=sanit_name, path=path,
                                                          image_name=template.macroimage_name()))

        if not params.local_image:
            print("Push the new image into registry\n"
                  "  docker push {}".format(template.macroimage_name()))

    elif params.generator == "multivolume":
        dirs = [f for f in os.listdir(path)
                if os.path.isdir(os.path.join(path, f)) and not
                os.path.islink(os.path.join(path, f)) and
                len(os.listdir(os.path.join(path, f)))]

        template = MultivolumeTemplateGenerator(params.container_name,
                                                offline_os_version_detection(path),
                                                params.image_url,
                                                exposed_ports=params.tcp,
                                                exported_paths=dirs,
                                                external_ips=params.ip)

        write_file("{}/{}-svc.yaml".format(dest, sanit_name), template.generate_service_template())
        write_file("{}/{}-pod.yaml".format(dest, sanit_name), template.generate_pod_template())

        print("Create a tar image of migrated machine:\n"
              "  tar -czf {}/{}.tar.gz -C {} .\n\n"
              "Move it to the given location ({}),\n"
              "where it will be available for pod initialization."
              .format(dest, os.path.basename(params.image_url), path, params.image_url))

if __name__ == "__main__":
    main()
