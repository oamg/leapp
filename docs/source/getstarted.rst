Getting started
===============

Importing Apps with leapp
^^^^^^^^^^^^^^^^^^^^^^^^^

The migration prototype currently handles following:

* migrating from a CentOS 6 VM to a macrocontainer running on
  a CentOS 7 container host. Migration from Centos/RHEL 7 is coming soon.

Setting up to run leapp import tool
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Installation - CentOS 7
-----------------------
Install LeApp using these steps: ::

    sudo yum-config-manager --add-repo https://copr.fedorainfracloud.org/coprs/evilissimo/leapp-stable/repo/epel-7/evilissimo-leapp-stable-epel-7.repo
    sudo yum install epel-release
    sudo yum install leapp-cockpit

Installation - RHEL 7
---------------------
Install LeApp using these steps: ::

    sudo curl https://copr.fedorainfracloud.org/coprs/evilissimo/leapp-stable/repo/epel-7/evilissimo-leapp-stable-epel-7.repo -o /etc/yum.repos.d/evilissimo-leapp-stable-epel-7.repo
    sudo yum install http://dl.fedoraproject.org/pub/epel/7/x86_64/e/epel-release-7-10.noarch.rpm
    sudo subscription-manager --enable rhel-7-server-extras-rpms
    sudo yum install leapp-cockpit


Installation - Fedora 25
------------------------
Install LeApp using these steps: ::

    sudo dnf install dnf-plugins-core
    sudo dnf copr enable evilissimo/leapp-stable
    sudo dnf install leapp-cockpit


Latest development builds
-------------------------
You can find the latest development builds here:
    https://copr.fedorainfracloud.org/coprs/evilissimo/leapp


Enable and Start Docker & Cockpit
---------------------------------

    systemctl enable docker
    systemctl enable cockpit
    systemctl start docker
    systemctl start cockpit


Importing apps via the CLI
^^^^^^^^^^^^^^^^^^^^^^^^^^

First add your private key for accessing the source machine as root to your running ssh-agent to enable passwordless authentication

    /usr/bin/leapp-tool migrate-machine --use-rsync \
    --ignore-default-port-map \
    -t 127.0.0.1 source.myapp.com \
    --force-create

Note: replace source.myapp.com with IP/FQDN of your VM

Importing apps  via the Cockpit
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

YouTube Video: https://youtu.be/s4RY1PysHM4

First add your private key to your ssh-agent to enable passwordless authentificatoin::

Open Cockpit in your browser:

    http://localhost:9090

* Access cockpit plugin
  Select: 'Tools -> Import Apps'

* Specify Source IP/FQDN you are going tom import

* Scan the source and prepare target ( localhost )

  Click: "Find Apps"

* Wait until all commands are finished with no errors , in the console observe all commands become "black"

  Click "Import"

* Access your new App inside container



Known Constraints
^^^^^^^^^^^^^^^^^

Currently known constraints on this approach:

* SELinux process separation is not available inside the resulting macrocontainer


