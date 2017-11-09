# Developing harnessed jobs to run in the eTraveler

## Create a JH installation.

Create a JH installation area using the packageList from the release
package that corresponds to the software subsystem for which you want
to do development.  This helps ensure that all of the needed packages
and versions of those packages are installed.  This also creates a
setup script that you can use to set the runtime environment for the
JH code.

First, clone the release package:
```
$ git clone git@github.com:lsst-camera-dh/release.git
```

In order to enable development outside of the context of the eTraveler
web application, copy the desired packageList and add the jh-dev-tools
package under the [packages] section, if it isn't already there.
```
$ cp release/packageLists/IR2_JH_versions.txt ./my_jh_install.txt
$ grep jh-dev-tools my_jh_install.txt
jh-dev-tools = 0.0.1
```

Create the install folder, and run the install.py script (directing
the screen output to a log file):
```
$ mkdir jh_install
$ (release/bin/install.py --inst_dir jh_install my_jh_install.txt) >& jh_install/install.log
```

NB: If you will be running on a generic rhel6-64 machine at SLAC and
are installing the eotest 0.0.21 or earlier, you'll need to enable
devtoolset-3 in order to get a gcc version compatible with the LSST
Stack:
```
$ scl enable devtoolset-3 bash
```
Later versions of eotest do not build against the Stack, so the newer
compiler version isn't needed.  The IR-2 diagnostic cluster has a
sufficiently recent gcc version.

Note also that the LSST Stack installation is specified in the
packageList file.  The Stack for use on the IR-2 machines,
```
$ grep stack_dir my_jh_versions.txt
stack_dir = /lsst/dh/software/centos7-gcc48/anaconda/py-2.7/envs/v12_0
```
is not accessible from generic rhel6-64 machines at SLAC.

## Git clone the package you want to work on.

Move the package(s) you wish to work on out of the way, git clone the
package repository to the JH install area, and symlink it to the
versioned name, e.g.,
```
$ cd jh_install
$ mv IandTjobs-0.0.3 IandTjobs-0.0.3_orig
$ git clone git@github.com:lsst-camera-dh/IandT-jobs.git
$ ln -s IandT-jobs IandTjobs-0.0.3
```

## Work on a development branch, do not push directly to master.

Before doing any development, create a branch off of master for your
work:
```
$ cd IandT-jobs
$ git checkout master         # you should already be on master
$ git checkout -b LSSTTD-xxx
```
or
```
$ git checkout -b u/jchiang/ts8_pd_calibration
```
If there is a JIRA issue for the work, include the issue ID in the
branch name so that it is automatically linked to the JIRA issue.  If
the work has no specific JIRA issue, prepend a descriptive name with
`u/<user_id>/` so that those development branches are organized by
user id when listed.

## Create a folder/subdirectory for your new harnessed job.

Create a subdirectory with the harnessed job name in the harnessed_jobs
subfolder of the package you're working on:
```
$ mkdir -p harnessed_jobs/ts8_pd_calibration/v0
```
For historical reasons, every harnessed job needs to have a v#
subdirectory.  In practice, this is always "v0".

## Create/copy the standard files for a harnessed job.

Every harnessed job needs three files: `modulefile`,
`producer_<jobname>.py`, `validator_<jobname>.py`.  It may be useful to
copy from an existing job and rename and edit the files:
```
$ cd harnessed_jobs/ts8_pd_calibration/v0
$ cp ../../rtm_aliveness_exposure/v0/modulefile .
$ sed s/rtm_aliveness_exposure/ts8_pd_calibration/g modulefile > tmp
$ mv tmp modulefile
$ cp ../../rtm_aliveness_exposure/v0/producer*.py producer_ts8_pd_calibration.py
$ cp ../../rtm_aliveness_exposure/v0/validator*.py validator_ts8_pd_calibration.py
```
The python scripts will need context-specific editing.

## Jython scripts for commanding CCS.

For jobs that need to send commands to CCS, the convention is to put
that code in a jython script called "ccs_<jobname>.py":
```
$ cp ../../rtm_aliveness_exposure/v0/ccs*.py ccs_ts8_pd_calibration.py
```

In these cases, the producer script will often just contain code that
dispatches the jython commands to CCS via boiler-plate code:
```
$ cat producer_ts8_pd_calibration.py
#!/usr/bin/env python
from ccsTools import ccsProducer, CcsRaftSetup

ccsProducer('ts8_pd_calibration', 'ccs_ts8_pd_calibration.py',
            ccs_setup_class=CcsRaftSetup,
            sys_paths=(os.path.join(os.environ['IANDTJOBSDIR'], 'python'),))
```
The `sys_paths` keyword argument allows one to specify directory paths
to any _jython_ modules that the jython script called by the
`ccsProducer` function would call.  Note that the jython scripts do
not share the same python environment as the `producer` and
`validator` scripts, so the paths to any user-provided jython modules
need to be added via this keyword.

Note also that the jython scripts are not executed on one of the
usual IR-2 login nodes (e.g., lsst-dc10 or lsst-it01).  This means
that the harnessed job code has to be installed on a file system that
can be seen from all of the IR-2 machines.  In practice, any JH
development code should be installed in the `/lnfs/lsst/devel` area.

## Using GitHub Flow for development.

We (try to) use [GitHub
Flow](https://guides.github.com/introduction/flow/) for managing
development.  The basic procedure consists of committing changes to a
branch off of master, pushing to that branch on git-hub, opening a
pull-request to discuss changes or to submit the code for review.
Once the code has been reviewed and approved, the developer merges it
into master.  Generally, new development should have unit tests, and
it definitely should not "break" master if merged.  Once merged into
master, the branch should be deleted (to avoid any more development on
that branch), and once any other changes have been merged, a release
of the package is made.  Developers are free to create beta releases
on their development branch so that the install.py script can be used
to make a preliminary release candidate installation for testing
against the dev eTraveler instance.

A typical development session might look like this:
```
$ <edit some files>
$ git add -p       # select changes to stage for committing
$ git commit -m "<a helpful description of the changes>"
<...additional work and commits...>
$ git push
```

If this is the first set of commits on this branch to be pushed to GitHub,
the push command will need to set the branch name on GitHub, e.g.,
```
$ git push -u origin u/jchiang/ts8_pd_monitoring
```
It is best to use `git add -p` to avoid committing unintended files
from being staged (and subsequently committed and pushed).  Unstaged
diffs can be viewed with `git diff` while staged diffs can be viewed
with `git diff --staged`.

Generally speaking, it is better not to let development linger on a
branch for too long as the code on master will evolve and
inconsistencies with the old code on the branch may arise, thereby
making it difficult to reconcile with the current master.
