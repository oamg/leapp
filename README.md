# Macrocontainers for Legacy Applications

LeApp is a "Minimum Viable Migration" utility that aims to
decouple virtualized applications from the operating system
kernel included in their VM image by migrating them into
macrocontainers that include all of the traditional components
of a stateful VM (operating system user space, application
runtime, management tools, configuration files, etc), but
use the kernel of the container host rather than providing
their own.

## Migration prototype

The migration prototype currently handles exactly one case:
migrating from a CentOS 7 VM to a macrocontainer running on
a CentOS 7 container host.

### Setting up to run the prototype demonstration

The prototype requires Vagrant with some relevant plugins:

    $ sudo vagrant plugin install ansible hitimes nio4r

It also requires the virt-inspector tool:

    $ sudo yum install libguestfs-tools-c

Start the source application server VM:

    $ pushd ansible/rhel6-guest-lamp
    $ sudo vagrant up
    $ popd

Start the target container host VM:

    $ pushd ansible/rhel7-target
    $ sudo vagrant up
    $ popd

The `start_vms.sh` helper script encapsulates these steps.

Use `sudo vagrant destroy` and `sudo vagrant up` in the
`ansible/rhel7-target` directory to reset the VM state
before running the demonstration again.

### Running the demonstration via the CLI

First, check that the source VM is showing the
PHP admin login page, while the target VM isn't
running a HTTP server.

The demo admin login credentials are:

* Username: `root`
* Password: `toor`

Then, from the base of the local clone, run:

    $ sudo ./leapp-tool.py migrate-machine -t rhel7-target rhel6-app-vm

The target VM should now be showing the PHP admin page,
with the same information as the source VM.


### Running the demonstration via Cockpit

Link the Cockpit plugin (if not already linked):

    $ mkdir -p ~/.local/share/cockpit
    $ ln -snf $PWD/cockpit ~/.local/share/cockpit/leapp

Link the `leapp` project directory (if not already linked):

    $ sudo ln -snf $PWD /opt/leapp

Open Cockpit in your browser:

    http://localhost:9090

When authenticating, check the option to allow
Cockpit to retain your password for later
privilege escalation.

Open "Tools->Kernel Flexibility" from the
navigation menu.

Check that the application link for the source VM
show the PHP info page, while the target VM isn't
running a HTTP server.

Click the "Migrate" button (this is currently
hardcoded to migrate `rhel6-app-vm` to `rhel7-target`)

The target VM should now be showing the PHP info page,
with the same information as the source VM.


Known Constraints
-----------------

Currently known constraints on this approach:

* Migration currently only works for source VMs using
  systemd as their init system
* SELinux process separation is not available inside
  the resulting macrocontainer