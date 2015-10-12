#!/usr/bin/env python
"""
Let's pretend we are the eTraveler.

This provides an HTTP server that tries mightily to pretend to be like
the real eTraveler web app.
"""

import os
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import cgi
import json
import time
import collections
from sys import stderr
import pickle
import logging

logging.basicConfig(filename='fakelims.log', level=logging.DEBUG)

def check_traveler(traveler_data, verbose=True):
    """
    Check that the dependencies in the dictionary representation of a
    fakelims traveler are consistent.
    """
    if not isinstance(traveler_data, dict):
        # Assume this is an python module, so import the traveler_data
        # dictionary.
        if verbose:
            print "Checking %s..." % traveler_data
        exec('from %s import traveler_data' % traveler_data.split('.py')[0])
    #
    # Loop over dependencies for each task and check that the
    # dependency exists as a task.
    for keys, values in traveler_data.items():
        for value in values:
            # This will raise a KeyError exception if the target task
            # is missing:
            traveler_data[value]
    return traveler_data

class FakeTraveler(object):
    default_traveler = {
        ('example_station_A','v0'): (('example_station_B','v0'),
                                     ('example_ana_A','v0')),
        }
    def __init__(self, traveler_data=None):
        if not traveler_data:
            print "FakeTraveler: Using default_traveler"
            traveler_data = FakeTraveler.default_traveler
        traveler_data = check_traveler(traveler_data)
        self.traveler = traveler_data
        deps = collections.defaultdict(list)
        for parent, daughters in traveler_data.iteritems():
            logging.debug('parent:"%s", daughters="%s"' % (parent, daughters))
            for d in daughters:
                deps[d].append(parent)
        self.dependencies = deps
        return

    def __str__(self):
        return '<FakeTraveler traveler="%s" dependencies="%s">' % \
            (self.traveler, self.dependencies)

    def prereq(self, name, version):
        return self.dependencies.get((name,version))

    pass

class FakeLimsDB(object):
    '''
    A fake LIMS database for testing the job harness
    '''
    def __init__(self, path):
        self.path = path
        try:
            # Load dictionaries of job parameters.
            self.jobregs = pickle.load(open(self.path))
        except IOError:
            # Create from scratch.
            self.jobregs = []
        self.status = collections.defaultdict(list) # indexed by jobids

    def register(self, **kwds):
        """
        Register a jobs information, return job ID
        """
        jobid = len(self.jobregs)
        self.jobregs.append(dict(kwds, jobid=jobid))
        return jobid

    def registration(self, jobid):
        """
        Return registration information for given jobid
        """
        try:
            reg = self.jobregs[jobid]
        except IndexError:
            return None
        return reg

    def lookup(self, **kwds):
        """
        Return first jobid that matches given keyword arguments.
        """
        logging.debug('JOBREGS: %s' % str(self.jobregs))

        tomatch = set(kwds.items())
        logging.debug('TOMATCH: %s' % str(tomatch))
        for ind, jr in enumerate(self.jobregs):
            jrs = set(jr.items())
            logging.debug('JR: %s' % str(jrs))
            if tomatch.issubset(jrs):
                return ind
        return None
        
    def update(self, jobid, state, status):
        """
        Update the status of the jobid
        """
        self.status[jobid].append(dict(state=state,
                                       status=status,
                                       stamp=time.time()))
        return

    def persist(self):
        print "Persisting db object in", self.path
        output = open(self.path, 'w')
        pickle.dump(self.jobregs, output)
        output.close()

    pass

class FakeLimsCommands(object):
    
    # function: [expected, args]
    API = {
        'requestID': ['stamp','unit_type','unit_id', 'job',
                      'version', 'operator'],
        'update': ['jobid','stamp','step','status'],
        'ingest': ['jobid','stamp','result'],
        'status': ['jobid','status'],
        }

    def __init__(self, traveler_data=None):
        dbfile = '.'.join(traveler_data.split('.')[:-1]) + '.db'
        print "dbfile:", dbfile
        self.db = FakeLimsDB(dbfile)
        self.traveler = FakeTraveler(traveler_data=traveler_data)
        logging.debug('TRAVELER: "%s"' % str(self.traveler))
        return

    def __call__(self, cmd, **kwds):
        meth = eval('self.cmd_%s'%cmd)
        return meth(**kwds)

    def cmd_requestID(self, unit_type, unit_id, job, version, operator,
                      stamp, jobid=None):
        "Register a job, get a job ID"

        ret = []
        prereqs = self.traveler.prereq(job, version)
        logging.debug('PREREQS=%s' % str(prereqs))

        if prereqs:
            for pr in prereqs:
                jn,jv = pr
                tofind = dict(unit_type=unit_type, unit_id=unit_id,
                              job=jn, version=jv)
                jid = self.db.lookup(**tofind)
                if jid is None:
                    msg = 'Failed to find prerequisite: %s'%str(tofind)
                    logging.error(msg)
                    return {'jobid':None, 
                            'error':msg}
                job_info = self.db.registration(jid)
                ret.append(job_info)
                continue

        jobid = self.db.register(unit_type=unit_type, unit_id=unit_id, 
                                 job=job, version=version, operator=operator)

        return {'jobid':jobid, 'prereq':ret}

    def cmd_update(self, step, status, stamp, jobid):
        "Update status for jobid step"
        self.db.update(jobid, step, status)
        return {'acknowledge': None}

    def cmd_ingest(self, result, stamp, jobid):
        "Ingest the result summary data."
        logging.info('Result from jobid %d at %s:'
                     % (jobid, time.asctime(time.localtime(stamp))))
        logging.info(str(result))
        return {'acknowledge': None}

    def cmd_status(self, status, jobid):
        "Retrieve status of given job and status type"
        logging.info('Status request of type "%s" from jobid %d'
                     % (status, jobid))
        meth = eval('self.cmd_status_%s' % status)
        return meth(jobid)

    def cmd_status_registration(self, jobid):
        jr = self.db.registration(jobid)
        if not jr:
            return dict(jobid=jobid, status='registration',
                        error='No such jobid')
        ret = [jr]
        prereqs = self.traveler.prereq(jr['job'],jr['version']) or []
        for pr_name, pr_ver in prereqs: 
            tofind = dict(jr, job=pr_name, version=pr_ver)
            jid = self.db.lookup(**tofind)
            if jid is None:
                msg = 'Failed to find prerequisite: %s'%str(tofind)
                logging.error(msg)
                return {'jobid':None, 
                        'error':msg}
            job_info = self.db.registration(jid)
            ret.append(job_info)
            continue
        # fixme ^^^ refactor out this copy-pasta with cmd_requestID()
        return dict(jobid=jobid, status='registration', prereq=ret)

    def cmd_status_update(self, jobid):
        s = self.db.status[jobid]
        r = dict(jobid=jobid, status='update')
        if not s:
            r['error'] = ('acknowledge',
                          'No status registered for jobid %d' % jobid)
        else:
            r['steps'] = s
        return r

    pass

class FakeLimsHandler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        res = 'POST only, man!\n'
        self.wfile.write(res)
        return


    def postvars(self):
        """
        Return a dictionary of query parameters
        """
        ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
        logging.debug('ctype="%s" pdict="%s"' % (str(ctype), str(pdict)))
        if ctype == 'multipart/form-data':
            postvars = cgi.parse_multipart(self.rfile, pdict)
        elif ctype == 'application/x-www-form-urlencoded':
            length = int(self.headers.getheader('content-length'))
            postvars = cgi.parse_qs(self.rfile.read(length),
                                    keep_blank_values=1)
        else:
            return {}
        query = {k:v[0] for k,v in postvars.iteritems()}
        js = query['jsonObject']
        return json.loads(js)

    def do_POST(self):

        # check against API
        cmd = self.path.split('/')[-1]
        try:
            api = lims_commands.API[cmd]
        except KeyError:
            self.set_error('Unknown command: "%s"' % cmd)
            return

        pvars = self.postvars()
        chirp = 'CMD:"%s" POSTVARS:"%s"' % (cmd,pvars)
        print chirp
        logging.debug(chirp)

        required_params = set(api)

        if not required_params.issubset(pvars):
            msg = 'Required params: %s' % str(sorted(required_params))
            log.error(msg)
            self.set_error(msg)
            return
        
        self.send_response(200)
        self.send_header('Content-type', 'text/json')
        self.end_headers()

        ret = lims_commands(cmd, **pvars)
        logging.debug('RET:%s'%str(ret))
        try:
            jstr = json.dumps(ret)
        except TypeError,msg:
            print 'Failed to dump to json for return from %s(%s)' \
                  % (cmd,str(pvars))
            raise
        self.wfile.write(jstr + '\n')
        return
        
    def set_error(self, msg):
        # use 412 for prereq not satisfied
        self.send_response(400)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(msg + '\n')
        return

    pass

if __name__ == '__main__':
    import sys
    lims_commands = FakeLimsCommands(traveler_data=sys.argv[1])

    try:
        server = HTTPServer(('', 9876), FakeLimsHandler)
        print 'started httpserver...'
        server.serve_forever()
    except KeyboardInterrupt:
        print '^C received, shutting down server'
        lims_commands.db.persist()
        server.socket.close()
