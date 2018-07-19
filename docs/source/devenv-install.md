# Installing the development environment

## RPM packages installation

If you do not want to modify the framework itself, install it from
the RPM packages provided by the [Copr](https://copr.fedorainfracloud.org/coprs/g/leapp/leapp-devel/)
build system, which automatically builds packages with every commit merged into master.
Packages are built for EPEL and Fedora.

```shell
    yum install -y yum-utils
    yum-config-manager --add-repo https://copr.fedorainfracloud.org/coprs/g/leapp/leapp-devel/repo/epel-7/group_leapp-leapp-devel-epel-7.repo
```

For the actor development, install the `leapp` and `snactor` tools. This pulls in also
`leapp-repository` with already existing actors, models, topic, tags and workflows.


```shell
    yum install snactor leapp
```

For the snactor development, install the `snactor` tool, and if you want to use actors, install also `leapp-repository`.

```shell
    yum install snactor leapp-repository
```

## Virtualenv installation

To keep your environment clean, use a virtualenv.

First, create a new virtual environment called "tut" and activate it:
```shell
	$ cd ~/devel
	$ virtualenv -p /usr/bin/python2.7 tut
	$ . tut/bin/activate
```

Then, install the framework by using the pip package management system:
```shell
	$ pip install git+https://github.com/leapp-to/leapp
```

Once the framework is installed in your virtual environment, you can use the snactor tool.
```shell
	$ snactor -h
    usage: snactor [-h] [--version] [--logger-config LOGGER_CONFIG]
                   [--config CONFIG] [--debug]
                   ...

    Optional arguments:
      -h, --help            show this help message and exit
      --version             show program's version number and exit
      --logger-config LOGGER_CONFIG
                            Allows to override the logger.conf location
      --config CONFIG       Allows to override the leapp.conf location
      --debug               Enables debug logging

    Main commands:

        new-tag             Create a new tag
        new-model           Creates a new model
        run                 Execute the given actor
        workflow            Workflow related commands
        new-topic           Creates a new topic
        messages            Messaging related commands
        discover            Discovers all available entities in the current
                            repository
        new-project         [DEPRECATED] Creates a new project
        repo                Repository related commands
        new-actor           Creates a new actor
```

### A screen cast of the steps above

<asciinema-player src="_static/screencasts/install.json"></ascinema-player>
