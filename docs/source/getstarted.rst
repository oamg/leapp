Getting started
===============

Migration prototype
^^^^^^^^^^^^^^^^^^^

The migration prototype currently handles exactly two cases:

* migrating from a CentOS 6 VM to a macrocontainer running on
  a CentOS 7 container host.
* migrating from a CentOS 7 VM to a macrocontainer running on
  a CentOS 7 container host.

Setting up to run the prototype demonstration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Installation - CentOS 7
-----------------------
Install LeApp-To using these steps: ::

    sudo yum-config-manager --add-repo https://copr.fedorainfracloud.org/coprs/evilissimo/leapp/repo/epel-7/evilissimo-leapp-epel-7.repo
    sudo yum install epel-release 
    sudo yum install leapp-cockpit 

Optional (Demo setup): ::

    sudo yum install centos-release-scl
    sudo yum install sclo-vagrant1 qemu libguestfs-tools-c libvirt libvirt-devel ruby-devel gcc qemu-kvm nmap libffi-devel
	
Enable vagrant software collection: ::

    scl enable sclo-vagrant1 bash

Installation - RHEL 7
-----------------------
Install LeApp-To using these steps: ::

    sudo curl https://copr.fedorainfracloud.org/coprs/evilissimo/leapp/repo/epel-7/evilissimo-leapp-epel-7.repo -o /etc/yum.repos.d/evilissimo-leapp-epel-7.repo
    sudo yum install http://dl.fedoraproject.org/pub/epel/7/x86_64/e/epel-release-7-9.noarch.rpm
    sudo subscription-manager --enable rhel-7-server-extras-rpms
    sudo yum install leapp-cockpit 

Optional (Demo setup): 

* Download and install Vagrant from official pages: ::

    https://www.vagrantup.com/downloads.html

* Install dependencies required by vagrant build: ::

    sudo yum install qemu libguestfs-tools-c libvirt libvirt-devel ruby-devel gcc qemu-kvm nmap libffi-devel
	

Installation - Fedora 25
------------------------
Install LeApp-To using these steps: ::

    sudo dnf install dnf-plugins-core 
    sudo dnf copr enable evilissimo/leapp
    sudo dnf install leapp-cockpit

Optional (Demo setup): ::
        
    sudo dnf install vagrant qemu libguestfs-tools-c libvirt libvirt-devel ruby-devel gcc qemu-kvm nmap libffi-devel


Preparation & Running the demo
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
If the integration tests haven't been run, first install the testing
instance of the CLI: ::

    pipsi --bin-dir $PWD/bin install --python `which python2.7` $PWD/src

The integration tests do this automatically, so this step can be skipped if
those have already been run.

Make sure the libvirt daemon is running and enabled: ::

    for i in start enable; do sudo systemctl $i libvirtd; done

The prototype requires Vagrant with some relevant plugins: ::

    sudo vagrant plugin install ansible hitimes nio4r vagrant-libvirt

And passwordless access to VM management operations: ::

    sudo usermod -aG vagrant,libvirt $USER

You will need to log out and back in again, or start a new user
session with `su $USER`, to get the new group memberships to take
effect.

Finally, start all the demonstration VMs by running: ::

    ln -s ../available/centos6-guest demo/vmdefs/enabled/
    ln -s ../available/centos7-target demo/vmdefs/enabled/
    sudo demo/vmctl.sh provision

This script iterates over all the subdirectories of `demo/vmdefs/emabled` and runs
`vagrant up --provision`.

Note that the VMs shall be started by the same user who will run the
demo, i.e. when using sudo to run the demo, one shall use sudo to
start the VMs as well.

Running the demonstration via the CLI
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

First, check that the source VM is showing the
PHP admin login page at port 9000, while the target VM isn't
running a HTTP server.

The demo admin login credentials are:

* Username: `root`
* Password: `toor`

Then, from the base of the local clone, run: ::

    sudo bin/leapp-tool migrate-machine --user vagrant \
        --identity integration-tests/config/leappto_testing_key \
        --tcp-port 9000:9000 -t centos7-target centos6-app-vm

The target VM should now be showing the PHP admin page,
with the same information as the source VM.


Running the demonstration via Cockpit
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Link the Cockpit plugin (if not already linked): ::

    mkdir -p ~/.local/share/cockpit
    ln -snf $PWD/cockpit ~/.local/share/cockpit/leapp

Link the `leapp` project directory (if not already linked): ::

    sudo ln -snf $PWD /opt/leapp

Open Cockpit in your browser:

    http://localhost:9090

When authenticating, check the option to allow Cockpit to retain your password for later
privilege escalation. Open **Tools->Le-App** from the navigation menu. Then check that the 
application link for the source VM show the PHP info page, while the target VM isn't
running a HTTP server.

Click the "Migrate" button (this is currently hardcoded to migrate `centos6-app-vm` to `centos7-target`)

The target VM should now be showing the PHP info page,
with the same information as the source VM.


Known Constraints
^^^^^^^^^^^^^^^^^

Currently known constraints on this approach: 

*   SELinux process separation is not available inside the resulting macrocontainer

Key limitations in the current implementation:

*   Remote access to systems requires Vagrant managed VMs running locally under libvirt
