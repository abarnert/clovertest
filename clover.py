#!/usr/bin/env python3

import csv
import logging
import os
import re
import sqlite3
import sys

def opendb():
    return sqlite3.connect('clover.db')

def read_format(format):
    with open(os.path.join('specs', f'{format}.csv'), encoding='utf-8') as f:
        for col in csv.DictReader(f):
            col['width'] = int(col['width'])
            yield col

_CONVERSIONS = {
    'INTEGER': int,
    'BOOLEAN': lambda x: bool(int(x)),
    'TEXT': str
    }
            
def read_datafile(fname, format):
    with open(fname, encoding='utf-8') as f:
        for line in f:
            logger.debug(f"'{line.rstrip()}'")
            pos = 0
            row = {}
            for col in format:
                value = line[pos:pos+col['width']].rstrip()
                value = _CONVERSIONS[col['datatype']](value)
                row[col['column name']] = value
                pos += col['width']
            yield row

def make_table(db, tablename, format):
    cols = ',\n'.join('{column name} {datatype}'.format_map(col) for col in format)
    sql = f'''CREATE TABLE IF NOT EXISTS {tablename} ({cols})'''
    logging.debug(f"'{sql}'")
    db.execute(sql)

rfname = re.compile(r'data/([A-Za-z0-9]+?)_(\d\d\d\d-\d\d-\d\d)\.txt')
def handle_datafile(db, fname):
    logger.info(f"data file '{fname}'")
    try:
        m = rfname.match(fname)
        formatname = m.group(1)
        logger.debug(f"reading format '{formatname}'")
        format = list(read_format(formatname))
        make_table(db, formatname, format)
        logger.debug("'BEGIN'")
        db.execute('BEGIN')
        cols = ', '.join(col['column name'] for col in format)
        vars = ', '.join('?' for col in format)
        sql = f'INSERT INTO {formatname} ({cols}) VALUES ({vars})'
        # NOTE: It might be slightly more efficient to use executemany here,
        # but this way we can log each row.
        try:
            for row in read_datafile(fname, format):
                values = list(row.values())
                logger.debug(f"'{sql}', {values}")
                db.execute(sql, values)
        except:
            logger.debug("'ROLLBACK'")
            db.execute('ROLLBACK')
        else:
            logger.debug("'COMMIT'")
            db.execute('COMMIT')
    except Exception as e:
        logger.exception(f"failed on data file '{fname}'")

def handle_dir(db, dname):
    for fname in os.listdir(dname):
        if fname.endswith('.txt'):
            handle_datafile(db, os.path.join(dname, fname))
 
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        filename='clover.log',
                        format='%(asctime)s:%(levelname)-8s:%(message)s')
    logger = logging.getLogger('clover')
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    logger.addHandler(console)
    path = os.path.abspath(os.path.dirname(sys.argv[0]))
    os.chdir(path)
    with opendb() as db:
        handle_dir(db, 'data')
