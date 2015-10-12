import subprocess

harnessed_jobs = [
    'test_job'
    ]

for job in harnessed_jobs:
    subprocess.check_call('lcatr-harness --job=%s' % job, shell=True)
