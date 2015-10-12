# jh-dev-tools

This package provides an infrastructure for testing harnessed jobs
under the lcatr-* code without having to run the eTraveler web
application and thereby avoids polluting the eTraveler db tables and
Data Catalog with test entries and files.

To use this package, one sets up a Job Harness runtime environment
(indicated below by a "[jh]$ " bash prompt), and adds this package's
bin and python folders to the PATH and PYTHONPATH environment
variables, respectively.

As usual, there must be a symlinks from the harnessed job folder to
the Job Harness share directory, so if the lcatr-harness command is
```
[jh]$ which lcatr-harness
<...JH runtime dir...>/bin/lcatr-harness
```
then the harnessed job directory would be symlinked under <...JH
runtime dir...>/share, e.g., for the test_job in the examples folder,
```
[jh]$ ln -s examples/test_job <...JH runtime dir...>/share
```

The config/lcatr.cfg file needs to be appropriately modified and
placed in the user's working directory; and from that directory, one
runs the fake eTraveler server, giving it the python version of the
traveler:
```
[jh]$ fake_eT.py test_job_traveler.py
dbfile: test_job_traveler.db
Checking test_job_traveler.py...
started httpserver...
```

In a separate window, the job under development can be then be
executed and it will communicate with the fake_eT.py http server:
```
[jh]$ lcatr-harness --job=test_job
logging to: 2015-10-12T100116us043432.log
Loaded configuration files: ./lcatr.cfg
Loading schema with schema path: "/nfs/slac/g/ki/ki18/jchiang/LSST/JobHarness/share/test_job/v0"
Step configure completed
Step register completed
Moved log to /nfs/slac/g/ki/ki18/jchiang/LSST/lsst-camera-dh/jh-dev-tools/work/ASPIC/CHIP00/test_job/v0/0/2015-10-12T100116us043432_0.log
Step stage completed
executing producer_test_job.py
Step produce completed
executing validator_test_job.py
<...more output...>
```
