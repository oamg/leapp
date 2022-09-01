## Debugging actors

### Snactor

The snactor tool is used to debug your actors. You can execute actors
and save their output, so that it can be consumed by other actors.
See [Storing messages in the repository data for reuse](messaging.html#storing-messages-in-the-repository-data-for-reuse).

Snactor checks for the `LEAPP_DEBUG` environment variable and has also
the --debug parameter which sets the environment variable to '1' when it is
used. In that case, it enables the debug logging, so that any actor that logs
to self.log.debug gets its output printed on the commandline.

### PyCharm / rpdb

You can configure PyCharm to debug by pointing it to the snactor path and passing the arguments on the command line.
The PyCharm debugger will also follow the child processes that are created by the snactor tool to execute the actor
in a sandboxed environment.

Not everywhere you'll have PyCharm at hand but vim/nc lightweight tandem is already in place in majority of cases.
It's possible to go minimal and debug actor execution with remote debugger like
[rpdb](https://pypi.org/project/rpdb/). The setup is as simple as:

1. Add breakpoint at the desired place in actor's code `import rpdb; rpdb.set_trace()`
2. Run snactor and wait till breakpoint is hit.
3. In a separate console connect to the debugger via network utility of your choice. The default port is 4444.

```nc localhost 4444```


### Initramfs

One of the biggest debugging challenges is exploring something in initramfs stage, as currently there is no network
connectivity (this might change soon though).

1. (can be skipped if you already ended up with an emergency console)
To get access to the emergency console right after leapp execution in initramfs stage has finished you should add an
`rd.break=leapp-upgrade` argument to the kernel commandline. One way to do this is by changing the code of the
[addupgradebootentry actor](https://github.com/oamg/leapp-repository/blob/master/repos/system_upgrade/common/actors/addupgradebootentry/libraries/addupgradebootentry.py#L23)

2. (can be skipped if you don't need any extra binaries) [TBD] Information on how to include additional binaries into
the initramfs

3. To get access to the common binaries change `PATH` accordingly. Setting
`PATH="$PATH:$PATH:/sysroot/bin:/sysroot/sbin:/sysroot/usr/bin"` should do the trick.

4. If the binaries are complaining about missing shared libraries, try changing root to /sysroot: `chroot /sysroot`

5. [TBD] Put info how to collect the logs

> **_NOTE:_** When working in initramfs stage you will need a serial console. Though openstack machines can provide
you with a novnc console, unless you need a shared dev environment consider using vagrant/libvirt.
