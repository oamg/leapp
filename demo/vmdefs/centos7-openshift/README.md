## OpenShift Vagrant Box

This Vagrant box provides pre-canned evnironment for developers targeting OpenShift.

### Installing OpenShift client tools

Install either via DNF/YUM from one of the curated repositories, or simply:

```bash
mkdir ~/.bin/
cd ~/.bin/
curl -L https://github.com/openshift/origin/releases/download/v1.5.0/openshift-origin-client-tools-v1.5.0-031cbe4-linux-64bit.tar.gz | tar xOz '*/oc' > oc
export PATH=$PATH:~/.bin
```

### Logging in

All applications should be created under the default `developer` user:

```bash
export BOX_IP=$(vagrant ssh-config | sed -n 's/\s*HostName \(.*\)/\1/p')
oc login -u developer -p developer https://$BOX_IP:8443/
```

### Performing Administrative Tasks

Administrative tasks in OpenShift can be performed by special user `system:admin`. Logging in as that user is limited
to certificate only authentication, so we need to get hold of the certificate first:

```bash
ssh $(vagrant ssh-config | awk 'FNR > 1 && NF { print "-o "$1"="$2 }') '' 'sudo cat /var/lib/origin/openshift.local.config/master/admin.kubeconfig' > admin.kubeconfig
```

Note that this isn't the certificate itself but rather OpenShift config file that contains the certificate, key data and some other data.
Now we just need to determine the IP of the box and do `oc login`:

```bash
export BOX_IP=$(vagrant ssh-config | sed -n 's/\s*HostName \(.*\)/\1/p')
oc login -u system:admin --config admin.kubeconfig https://$BOX_IP:8443/
```

We should be ready to administrate our OpenShift cluster now!
