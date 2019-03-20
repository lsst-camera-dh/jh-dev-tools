from __future__ import print_function
from collections import OrderedDict
#from eTravelerDb import eTravelerDb

class Traveler(list):
    def __init__(self, name, hardwareGroup, description,
                 instructions="No instructions",
                 version="1", db_info=None, stepPrefix=None):
        super(Traveler, self).__init__()
        self.name = name
        self.hardwareGroup = hardwareGroup
        self.description = description
        self.instructions = instructions
        self.version = version
        self.dbObject = None
        if db_info is not None:
            pass
#            self.dbObject = eTravelerDb(db_info)
        self.stepPrefix = stepPrefix
    def stepFactory(self, name, **kwds):
        if self.stepPrefix is not None:
            candidateName =  '_'.join((self.stepPrefix, name))
        else:
            candidateName = name
        process_step = ProcessStep(candidateName, **kwds)
        if self.dbObject is not None:
            processInfo = self.dbObject.processInfo(candidateName)
            if processInfo:
                process_step.set_isRefObject()
                print("process step '%s' already exists" % candidateName)
                print("process info:", processInfo)
        self.append(process_step)
        return process_step
    def __repr__(self):
        output = []
        output.append('%YAML 1.1')
        output.append('---\n')
        output.append('Name: ' + self.name)
        output.append('HardwareGroup: ' + self.hardwareGroup)
        output.append('Description: ' + self.description)
        output.append('InstructionsURL: ' + self.instructions)
        output.append('Version: ' + self.version)
        output.append('Sequence:')
        for item in self:
            output.append(str(item))
        return '\n'.join(output)
    def write_fake_eT_traveler(self, outfile):
        my_dict = dict()
        for item in self:
            my_dict[item.fakelims_id()] = []
            for pre_req in item.pre_reqs:
                my_dict[pre_req.fakelims_id()].append(item.fakelims_id())
        for item in self:
            my_dict[item.fakelims_id()] = tuple(my_dict[item.fakelims_id()])
        output = open(outfile, 'w')
        output.write('traveler_data = %s\n' % my_dict)
    def write_yml(self, outfile):
        output = open(outfile, 'w')
        output.write(str(self) + '\n')
        output.close()

class ProcessStep(object):
    _offset = "    "
    _type = "PROCESS_STEP"
    def __init__(self, name, version='v0', description=None, jh=True,
                 level=1):
        self.name = name
        self.version = version
        self.description = description
        self.jh = jh
        self.level = level
        self.pre_reqs = []
        self.isRefObject = False
    def set_isRefObject(self):
        self.isRefObject = True
    def fakelims_id(self):
        return '%s' % self.name, '%s' % self.version
    def add_pre_reqs(self, *pre_reqs):
        for item in pre_reqs:
            self.pre_reqs.append(item)
    def _pre_req_str(self):
        offset = self._offset*self.level
        output = []
        output.append(offset + "  -")
        indent = offset + self._offset
        output.append(indent + "PrerequisiteType: " + self._type)
        output.append(indent + "Name: " + self.name)
        output.append(indent + "UserVersionString: " + self.version)
        return '\n'.join(output)
    def __repr__(self):
        indent = lambda x=0 : self._offset*(self.level + x)
        output = []
        output.append(indent(-1) + "  -")
        output.append(indent() + "Name: " + self.name)
        if self.description is not None:
            output.append(indent() + "Description: " + self.description)
        output.append(indent() + "UserVersionString: " + self.version)
        if self.jh:
            output.append(indent() + "TravelerActions:")
            output.append(indent() + "  - HarnessedJob")
        if self.pre_reqs:
            output.append(indent() + "Prerequisites:")
        for item in self.pre_reqs:
            output.append(item._pre_req_str())
        return '\n'.join(output)
