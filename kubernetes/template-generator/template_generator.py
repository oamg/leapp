#!/usr/bin/env python

import re
import yaml
import json


class SanitizeException(Exception):
    pass


class TemplateGenerator(object):
    def __init__(self, container_name, system, exposed_ports=None, external_ips=None):
        """
            @param string container_name    the name of migrated container
            @param ContainerOS system       a os description module
            @param list exposed_ports       a list of exposed ports
        """
        self.container_name = self.sanitize_container_name(container_name)
        self.system = system
        self.exposed_ports = exposed_ports
        self.external_ips = external_ips

    def generate_service_template(self, yaml=True):
        """
            Generate a YAML template for kerberos service
            @param Boolean yaml     if true, the output will be in yaml, else a
                                    dict will be returned


            @return string          a template string in yaml format/dict
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

        if self.external_ips is not None:
                service_template["spec"]["externalIPs"] = self.external_ips

        if self.exposed_ports is not None and len(self.exposed_ports) > 0:
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
            Generate a YAML template for kerberos pod
            @param Boolean yaml     if true, the output will be in yaml, else a
                                    dict will be returned

            @return string          a template string in yaml format/dict
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

            @param string name      a name to be sanitized
            @return string          a sanitized name

            @throw SanitizeException
        """
        if not len(name):
            raise SanitizeException("Name cannot be empty")

        # RE: [a-z0-9]([-a-z0-9]*[a-z0-9])? / RFC1123

        # Replace invalid characters and remove leading -
        found_name = re.findall("^-*([a-z0-9][a-z0-9-]*)*$", re.sub("[^0-9a-z]", "-", name))

        if len(found_name) >= 1:
            rev_name = found_name[0][::-1]
            return re.findall("^-*([a-z0-9][a-z0-9-]*)*$", rev_name)[0][::-1]
        else:
            raise SanitizeException("Name could not be sanitized")

    @staticmethod
    def _dump_yaml(data):
        """
            Converts dictionary (/object) to yaml

            @param dict data    the data which will be converted
            @return string      data in yaml format
        """
        return yaml.dump(data, default_flow_style=False)


class MacroimageTemplateGenerator(TemplateGenerator):
    def __init__(self, container_name, system, exposed_ports=None, external_ips=None, is_local=False):
        """
            @param string container_name    the name of migrated container
            @param ContainerOS system       a os description module
            @param list exposed_ports       a list of exposed ports
            @param Boolean is_local         disable pulling the image from registry on node
        """
        TemplateGenerator.__init__(self, container_name, system, exposed_ports, external_ips)

        self.is_local = is_local

    def macroimage_name(self):
        """
            generate docker image name
        """
        return "leapp/{}".format(self.container_name)

    def generate_pod_template(self, yaml=True):
        """
            Generate a YAML template for kerberos pod
            @param Boolean yaml     if true, the output will be in yaml, else a
                                    dict will be returned

            @return string          a template string in yaml format/dict
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

            @return string  a dockerfile content
        """
        # TODO: This can be done better if the image is being build on the same machine
        #       where the leapp tool is running
        path = "{}.tar.gz".format(self.container_name)
        content = "FROM {0}\nADD {1} /".format(self.system.base_image(), path)

        return content


class MultivolumeTemplateGenerator(TemplateGenerator):
    FORBIDDEN_MOUNTS = ["dev", "sys", "proc", "lost+found"]

    def __init__(self, container_name, system, image_url, exposed_ports=None, external_ips=None,
                 exported_paths=None):
        """
            @param string container_name    the name of migrated container
            @param ContainerOS system       a os description module
            @param string image_url         an URL to tar image containing the container FS
            @param list exported_paths      a list of all paths for which should be created a volume
            @param list exposed_ports       a list of exposed ports
        """
        TemplateGenerator.__init__(self, container_name, system, exposed_ports, external_ips)

        if exported_paths is None or len(exported_paths) == 0:
            raise AttributeError("Exported paths has to be set")

        if not len(image_url):
            raise AttributeError("image_url cannot be empty")

        self.image_url = image_url
        self.exported_paths = list(exported_paths)

        # Not allowed paths
        for FORBIDDEN_MOUNT in self.FORBIDDEN_MOUNTS:
            try:
                self.exported_paths.remove(FORBIDDEN_MOUNT)
            except Exception:
                pass

    def generate_pod_template(self, yaml=True):
        """
            Generate a YAML template for kerberos pod
            @param Boolean yaml     if true, the output will be in yaml, else a
                                    dict will be returned

            @return string/dict    a template string in yaml format/dict
        """
        def _generate_common_mounts(prefix="", mounts=None):
            """
                Generate mounts for a container

                @param string prefix    a prefix path for each generated mount
                @param list mounts      a list of mounts (optional)

                @return array           array of dicts describing mount points. If
                                        mounts was given, the returned array will be
                                        just a pointer to the same.
            """
            mounts = mounts or []

            for exported_path in self.exported_paths:
                vol_name = "{}-{}-vol".format(self.container_name, exported_path)

                if not len([mount for mount in mounts if mount["name"] == vol_name]):
                    mounts.append({
                        "name": vol_name,
                        "mountPath": "{}/{}".format(prefix, exported_path)
                    })
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
        for exported_path in self.exported_paths:
            vol_name = "{}-{}-vol".format(self.container_name, exported_path)

            if not len([i for i in pod_template["spec"]["volumes"] if i["name"] == vol_name]):
                pod_template["spec"]["volumes"].extend([{
                    "name": vol_name,
                    "emptyDir": {}
                }])
            else:
                print("W: Ignoring {} since it already exists".format(vol_name))

        if yaml:
            return self._dump_yaml(pod_template)

        return pod_template
