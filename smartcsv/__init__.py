# -*- coding: utf-8 -*-

"""
smartcsv: Smart CSV processing for humans.
~~~~~~~~~~~~~~~~~~~~~

smartcsv is a python utility to read and parse CSVs based on model definitions.
Instead of just parsing the CSV into lists (like the builtin csv module)
it adds the ability to specify models with attributes names.
On top of that it adds nice features like validation,
custom parsing, failure control and nice error messages.

:copyright: (c) 2014 by Santiago Basulto.
:license: MIT License, see LICENSE for more details.

"""

__title__ = 'smartcsv'
__version__ = '0.2.1'
__build__ = 0x000201
__author__ = 'Santiago Basulto'
__license__ = 'MIT'
__copyright__ = 'Copyright 2014 Santiago Basulto'

from .reader import CSVModelReader

reader = CSVModelReader
