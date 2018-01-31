#!/usr/bin/env python3

import os
import subprocess
import sys

os.remove('clover.db')
subprocess.check_call(['./clover'])
ret = subprocess.check_output(['sqlite3', 'clover.db', '-cmd',
                               'SELECT name, valid, count FROM testformat1 ORDER BY name'],
                              input='', encoding='utf-8')
ret = ret.splitlines()
assert ret == ['Barzane|0|-12', 'Foonyor|1|1', 'Quuxitude|1|103']
ret = subprocess.check_output(['sqlite3', 'clover.db', '-cmd',
                               'SELECT last, first, identity FROM superheroes ORDER BY last'],
                              input='', encoding='utf-8')
ret = ret.splitlines()
assert ret == ['Allen|Barry|Flash',
               "J'onzz|J'onn|Martian Ma",
               'Lance|Laurel|Black Cana',
               'Lance|Sara|White Cana',
               'Mxyzptlk|Mister|🙃ʞʃʇdzʎxW',
               'Na Wei|Chien|简娜伟',
               'Queen|Oliver|Green Arro',
               'Ramon|Cisco|Vibe',
               'Snow|Caitlin|Killer Fro',
               'Wells|Harrison|Reverse Fl',
               'West|Wally|Kid Flash',
               'Zor-El|Kara|Supergirl']
