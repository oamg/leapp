# Installation

## RPM packages installation

If you do not want to modify the framework itself, install it from
the RPM packages provided by the [Copr](https://copr.fedorainfracloud.org/coprs/g/oamg/leapp/)
build system, which automatically builds packages with every commit merged into main.
Packages are built for EPEL and Fedora.

* On CentOS/RHEL:
  ```shell
  # yum install -y yum-utils
  # yum-config-manager --add-repo https://copr.fedorainfracloud.org/coprs/g/oamg/leapp/repo/epel-8/group_oamg-leapp-epel-8.repo
  ```
* On Fedora:
  ```shell
  # dnf install -y dnf-plugins-core
  # dnf copr enable @oamg/leapp
  ```

For the actor development, install the `leapp` and `snactor` tools. This pulls in also
`leapp-repository` with already existing actors, models, topic, tags and workflows.


```shell
# yum install snactor leapp
```

For the actor development, install the `snactor` tool, and if you want to use actors, install also `leapp-repository`.

```shell
# yum install snactor leapp-repository
```

## Virtualenv installation

To keep your environment clean, use a virtualenv.

First, create a new virtual environment called "tut" and activate it:
```
$ cd ~/devel
$ virtualenv -p /usr/bin/python2.7 tut
$ . tut/bin/activate
```

Then, install the framework by using the pip package management system:
```shell
$ pip install git+https://github.com/oamg/leapp
```

Once the framework is installed, you can use the snactor tool.
```
$ snactor --help
usage: snactor [-h] [--version] [--logger-config LOGGER_CONFIG]
               [--config CONFIG] [--verbose] [--debug]
               ...

Optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  --logger-config LOGGER_CONFIG
                        Allows to override the logger.conf location
  --config CONFIG       Allows to override the leapp.conf location
  --verbose             Enables verbose logging
  --debug               Enables debug mode

Main commands:

    new-tag             Create a new tag
    new-model           Creates a new model
    run                 Execute the given actor
    workflow            Workflow related commands
    new-topic           Creates a new topic
    messages            Messaging related commands
    discover            Discovers all available entities in the current
                        repository
    new-project         [DEPRECATED] Creates a new repository
    repo                Repository related commands
    new-actor           Creates a new actor
```

### A screen cast of the steps above

<asciinema-player src="_static/screencasts/install.json"></ascinema-player>
