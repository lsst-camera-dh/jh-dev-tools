#!/usr/bin/env python
import os
import lcatr.schema

print "executing validator_test_job.py"

print lcatr.schema.__file__

for item in os.environ.keys():
    if item.find('LCATR') != -1:
        print item, os.environ[item]

results = [lcatr.schema.valid(lcatr.schema.get('test_job'), status=0)]

filename = 'foo.txt'
results.append(lcatr.schema.fileref.make('foo.txt',
                                         metadata=dict(DATA_PRODUCT='example_file')))

lcatr.schema.write_file(results)
lcatr.schema.validate_file()
