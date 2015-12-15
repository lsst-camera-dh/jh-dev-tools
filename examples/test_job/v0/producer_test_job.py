#!/usr/bin/env python
import subprocess

print "executing producer_test_job.py"

subprocess.call('touch foo.txt', shell=True)

