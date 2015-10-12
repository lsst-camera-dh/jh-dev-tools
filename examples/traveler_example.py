"""
Example usage of the eTravelerComponents.py module for generating yaml
definitions of eTraveler processes and equivalent python-based
representations for running under fake_eT.py.
"""
import os
from eTravelerComponents import Traveler

traveler_name = 'example_traveler'
hardwareGroup = 'example_hardwareGroup'
description = 'This is an example process traveler.'
instructions = ''
version = "1"

example_traveler = Traveler(traveler_name, hardwareGroup, description,
                            instructions=instructions, version=version)

acquisition = example_traveler.stepFactory('data_acq',
                                           description='Acquire some data')

analysis1 = example_traveler.stepFactory('data_analysis_1',
                                         description='First part of data analysis')
analysis1.add_pre_reqs(acquisition)

analysis2 = example_traveler.stepFactory('data_analysis_2',
                                         description='Second part of data analysis')
analysis2.add_pre_reqs(acquisition, analysis1)

example_traveler.write_yml('example_traveler.yml')
example_traveler.write_fake_eT_traveler('example_traveler.py')
