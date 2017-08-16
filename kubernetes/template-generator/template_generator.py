#!/usr/bin/env python

import re
import os
import yaml
import json


class SanitizeException(Exception):
    pass


class TemplateGenerator(object):
    def __init__(self, container_name, system, exposed_ports=None, external_ips=None, loadbalancer=False):
        """
        :param container_name: the name of migrated container
        :type container_name: string
        :param system: a os description module
        :type system: ContainerOS
        :param exposed_ports: a list of exposed ports
        :type exposed_ports: list[tupple(int,int)]
        :param external_ips: a list of IP addreesses on which the port
            will be opened
        :type external_ips: list[string]
        :param loadbalancer: enable default external load balancer for services
        :type loadbalancer: bool
        """
        self.container_name = self.sanitize_container_name(container_name)
        self.system = system
        self.exposed_ports = exposed_ports
        self.external_ips = external_ips
        self.loadbalancer = loadbalancer

    def generate_service_template(self, yaml=True):
        """
        Generate a YAML template for kubernetes service

        :param yaml: if true, the output will be in yaml, else dict will be returned
        :type yaml: bool

        :return: a template string in yaml format/dict when "yaml" parameter is set, else an
            dict is returned.
        :rtype: string or dict
        """
        service_template = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": "leapp-{}-service".format(self.container_name),
                "labels": {
                    "name": "leapp-{}-label".format(self.container_name),
                    }
                },
            "spec": {
                "selector": {
                    "name": "leapp-{}-label".format(self.container_name),
                    },
            }
        }

        if self.external_ips and not self.loadbalancer:
            service_template["spec"]["externalIPs"] = self.external_ips
        elif self.loadbalancer:
            service_template["spec"]["type"] = "LoadBalancer"

        if self.exposed_ports:
            ports_template = {
                "ports": []
            }

            for pmap in self.exposed_ports:
                port = {
                    "port": pmap[0],
                    "targetPort": pmap[1],
                    "protocol": "TCP",
                    "name": "leapp-{}-{}-{}-port".format(self.container_name, pmap[0], pmap[1])
                }
                ports_template["ports"].append(port)

            service_template["spec"].update(ports_template)

        if yaml:
            return self._dump_yaml(service_template)

        return service_template

    def generate_pod_template(self, yaml=True):
        """
        Generate a YAML template for kubernetes pod

        :param yaml: if true, the output will be in yaml, else dict will be returned
        :type yaml: bool

        :return: a template string in yaml format/dict when "yaml" parameter is set, else an
            dict is returned.
        :rtype: string or dict
        """
        pod_template = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {
                "name": "leapp-{}-pod".format(self.container_name),
                "labels": {
                    "name": "leapp-{}-label".format(self.container_name),
                },
                "annotations": {
                }
            },
            "spec": {
                "containers": [
                    {
                        "name": "{}".format(self.container_name),
                        "image": self.system.base_image(),
                        "volumeMounts": []
                    }
                ],
                "volumes": []
            }
        }

        # Generate port list
        if self.exposed_ports is not None and len(self.exposed_ports) > 0:
            ports_template = {
                "ports": []
            }

            for pmap in self.exposed_ports:
                port = {
                    "containerPort": pmap[1],
                }
                ports_template["ports"].append(port)

            pod_template["spec"]["containers"][0].update(ports_template)

        # Systemd additions
        if self.system.is_systemd():
            systemd_mounts = [{
                "name": "{}-cgroup-vol".format(self.container_name),
                "mountPath": "/sys/fs/cgroup",
                "readOnly": True
            }]

            systemd_volumes = [{
                "name": "{}-cgroup-vol".format(self.container_name),
                "hostPath": {
                    "path": "/sys/fs/cgroup"
                }
            }]

            for mount in ["run", "tmp"]:
                systemd_mounts.append({
                    "name": "{}-{}-vol".format(self.container_name, mount),
                    "mountPath": "/{}".format(mount)
                })

                systemd_volumes.append({
                    "name": "{}-{}-vol".format(self.container_name, mount),
                    "emptyDir": {
                        "medium": "Memory"
                    }
                })

            pod_template["spec"]["containers"][0]["volumeMounts"].extend(systemd_mounts)
            pod_template["spec"]["volumes"].extend(systemd_volumes)

        if yaml:
            return self._dump_yaml(pod_template)

        return pod_template

    @staticmethod
    def sanitize_container_name(name):
        """
        Convert container name to RFC1123 form

        :param name:  a name to be sanitized
        :type name: string

        :return: sanitized name
        :rtype: string

        :raises SanitizeException: in case the name could not be sanitized
        """
        if not len(name):
            raise SanitizeException("Name cannot be empty")

        # RE: [a-z0-9]([-a-z0-9]*[a-z0-9])? / RFC1123

        # Replace invalid characters and remove leading -
        found_name = re.findall("^-*([a-z0-9][a-z0-9-]*)*$", re.sub("[^0-9a-z]", "-", name))

        if len(found_name):
            rev_name = found_name[0][::-1]
            return re.findall("^-*([a-z0-9][a-z0-9-]*)*$", rev_name)[0][::-1]
        else:
            raise SanitizeException("Unable to sanitize name \"{}\". "
                                    "Name must contain alphabetical charactes and cannot begin with number")

    @staticmethod
    def _dump_yaml(data):
        """
        Converts dictionary (/object) to yaml

        :param data: the data which will be converted
        :type data: dict


        :returns: data in yaml format
        :rtype: string

        """
        return yaml.dump(data, default_flow_style=False)


class MacroimageTemplateGenerator(TemplateGenerator):
    def __init__(self, container_name, system, exposed_ports=None, external_ips=None, loadbalancer=False,
                 is_local=False):
        """
        :param container_name: the name of migrated container
        :type container_name: string
        :param system: a os description module
        :type system: ContainerOS
        :param exposed_ports: a list of exposed ports
        :type exposed_ports: list[tupple(int,int)]
        :param external_ips: a list of IP addreesses on which the port
            will be opened
        :type external_ips: list[string]
        :param loadbalancer: enable default external load balancer for services
        :type loadbalancer: bool
        :param is_local: disable pulling the image from registry on node
        :type is_local: bool
        """
        super(MacroimageTemplateGenerator, self).__init__(container_name, system, exposed_ports, external_ips,
                                                          loadbalancer)

        self.is_local = is_local

    def macroimage_name(self):
        """
        generate docker image name
        """
        return "leapp/{}".format(self.container_name)

    def generate_pod_template(self, yaml=True):
        """
        Generate a YAML template for kubernetes pod

        :param yaml: if true, the output will be in yaml, else dict will be returned
        :type yaml: bool

        :return: a template string in yaml format/dict when "yaml" parameter is set, else an
            dict is returned.
        :rtype: string or dict
        """
        pod_template = TemplateGenerator.generate_pod_template(self, False)

        pod_template["spec"]["containers"][0]["image"] = self.macroimage_name()

        if self.is_local:
            pod_template["spec"]["containers"][0]["imagePullPolicy"] = "Never"

        if yaml:
            return self._dump_yaml(pod_template)

        return pod_template

    def generate_dockerfile(self):
        """
        Method generate Dockerfile for macroimage. The dockerfile expects the tar file
        in the same directory (scope) names as: sanitized-container-name.tar.gz

        :returns: a dockerfile content
        :rtype: string
        """
        # TODO: This can be done better if the image is being build on the same machine
        #       where the leapp tool is running
        path = "{}.tar.gz".format(self.container_name)
        content = "FROM {0}\nADD {1} /".format(self.system.base_image(), path)

        return content


class InvalidVolumeMount(ValueError):
    pass


class ForbiddenVolumeMount(ValueError):
    pass


class MultivolumeTemplateGenerator(TemplateGenerator):
    FORBIDDEN_MOUNTS = ["dev", "sys", "proc", "lost+found"]

    def __init__(self, container_name, system, image_url, exposed_ports=None, external_ips=None,
                 loadbalancer=False, exported_paths=None):
        """
        :param container_name: the name of migrated container
        :type container_name: string
        :param system: a os description module
        :type system: ContainerOS
        :param image_url: an URL to tar image containing the container FS
        :type image_url: string
        :param exposed_ports: a list of exposed ports
        :type exposed_ports: list[tupple(int,int)]
        :param external_ips: a list of IP addreesses on which the port
            will be opened
        :type external_ips: list[string]
        :param loadbalancer: enable default external load balancer for services
        :type loadbalancer: bool
        :param exported_paths: a list of all root paths for which should be created a volume. Path must be specified
            without leading /
        :type exposed_paths: list[string]

        :raises InvalidVolumeMount: if path is not root only
        :raises ForbiddenVolumeMount: if path is a forbidden mount (see
            MultivolumeTemplateGenerator.FORBIDDEN_MOUNTS)
        """
        super(MultivolumeTemplateGenerator, self).__init__(container_name, system, exposed_ports, external_ips,
                                                           loadbalancer)

        if not exported_paths:
            raise ValueError("Exported paths has to be set")

        if not image_url:
            raise ValueError("image_url cannot be empty")

        self.image_url = image_url
        self.exported_paths = list(exported_paths)

        for path in self.exported_paths:
            # Volumes can be only "root" paths.
            if os.path.basename(path) != path:
                raise InvalidVolumeMount(path)
            # Do not allow forbidden paths
            elif path in self.FORBIDDEN_MOUNTS:
                raise ForbiddenVolumeMount(path)

    def generate_pod_template(self, yaml=True):
        """
        Generate a YAML template for kubernetes pod

        :param yaml: if true, the output will be in yaml, else dict will be returned
        :type yaml: bool

        :return: a template string in yaml format/dict when "yaml" parameter is set, else an
            dict is returned.
        :rtype: string or dict
        """
        def _generate_common_mounts(prefix="", mounts=None):
            """
            Generate mounts for a container

            :param prefix: a prefix path for each generated mount
            :type prefix: string
            :param list mounts      a list of mounts (optional)
            :type mounts: list

            :returns: list of dicts describing mount points. If mounts was given, the returned array will be
                just a pointer to the same.
            :rtype: list
            """
            mounts = mounts or []
            generated_mounts = set(mount["name"] for mount in mounts)

            for exported_path in self.exported_paths:
                vol_name = "{}-{}-vol".format(self.container_name, exported_path)

                if vol_name not in generated_mounts:
                    mounts.append({
                        "name": vol_name,
                        "mountPath": "{}/{}".format(prefix, exported_path)
                    })
                    generated_mounts.add(vol_name)
                else:
                    print("W: Ignoring {} mount since it already exists".format(vol_name))

            return mounts

        init_template = [
            {
                "name": "{0}-init".format(self.container_name),
                "image": "busybox",
                "command": [
                    "sh", "-c",
                        "mkdir -p /work-dir && wget -O /work-dir/image.tar {} &&"
                        "cd /work-dir && tar -xf image.tar &&"
                        "mkdir -p /work-dir/var/log/journal/$(cat /work-dir/etc/machine-id)".format(self.image_url)
                    ],
                "volumeMounts": _generate_common_mounts("/work-dir")
            }
        ]

        pod_template = TemplateGenerator.generate_pod_template(self, False)
        pod_template["metadata"]["annotations"]["pod.beta.kubernetes.io/init-containers"] = json.dumps(init_template,
                                                                                                       sort_keys=True)

        _generate_common_mounts(mounts=pod_template["spec"]["containers"][0]["volumeMounts"])

        # Generate volumes
        generated_volumes = set(volume["name"] for volume in pod_template["spec"]["volumes"])

        for exported_path in self.exported_paths:
            vol_name = "{}-{}-vol".format(self.container_name, exported_path)

            if vol_name not in generated_volumes:
                pod_template["spec"]["volumes"].extend([{
                    "name": vol_name,
                    "emptyDir": {}
                }])
                generated_volumes.add(vol_name)
            else:
                print("W: Ignoring {} since it already exists".format(vol_name))

        if yaml:
            return self._dump_yaml(pod_template)

        return pod_template
