LeApp CI
========
LeApp CI is hosted on the [CentOS CI infrastructure](http://ci.centos.org/) using Jenkins and since
our tests are virtualization heavy we have a dedicated slave node (slave03) for our tests.

Architecture
^^^^^^^^^^^^

When Jenkins is triggered via a webhook it uses a Duffy key located in `~/duffy.key` to get a node from the CICO
cluster on which the test will run. Duffy is CentOS CI middleware for resource management inside the cluster.
The lifetime (read, debuggability) of a failed test run is 12 hours.

Configuration
^^^^^^^^^^^^^

All configuration regarding the CI can be found in the `centos-ci` directory where this readme is located.
Secrets and SSH keys can be found in the housekeeping repository.
The directory structure of `centos-ci` is as follows:

+-----------------------------+------------------------------------------------------------------------------+
| File/Directory              | Purpose                                                                      |
+=============================+==============================================================================+
| `ansible`                   | Playbook and roles setting up the test environment                           |
+-----------------------------+------------------------------------------------------------------------------+
| `jobs/integration_test.yml` | Jenkins Job Builder definition for our Jenkins job, more explanation below   |
+-----------------------------+------------------------------------------------------------------------------+
| `patches`                   | Any patches that we currently carry to make sure that test environment works |
+-----------------------------+------------------------------------------------------------------------------+
| `bootstrap.sh`              | Entry point of our CI, this is the first executed in a new test run          |
+-----------------------------+------------------------------------------------------------------------------+

Jenkins Job
^^^^^^^^^^^

Jenkins Job Builder file is a declarative way (YAML) of describing Jenkins Job, this file also describes who
can start test runs and what trigger phrase to use for PRs not by people from the admin list.

### Adding yourself to the list of people who can trigger a test run

Add your GitHub handle to the `admin-list` list under `jobs.triggers.github-pull-request` and open a PR with the change.

### The trigger phrase

We're currently using `*Jenkins: ok to test*` with asterisks being wildcards, when any user in the `admin-list` comments on a PR
with matching pattern a new test run will be scheduled.

### Updating the Jenkins Job

The job definition in Jenkins is updated periodically in 10 minutes intervals from **master** branch only. That means that for new
settings to take effect it needs to be merged into master first.
