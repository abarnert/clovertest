#!/usr/bin/env python3

import os
import subprocess
import sys

os.remove('clover.db')
subprocess.check_call([sys.executable, 'clover.py'])
ret = subprocess.check_output(['sqlite3', 'clover.db', '-cmd',
                               'SELECT name, valid, count FROM testformat1 ORDER BY name'],
                              input='', encoding='utf-8')
ret = ret.splitlines()
assert ret == ['Barzane|0|-12', 'Foonyor|1|1', 'Quuxitude|1|103']
