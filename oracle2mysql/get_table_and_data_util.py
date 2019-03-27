#!/usr/local/env python
# -*- coding: UTF-8 -*-
import os
import sys
import cx_Oracle

if sys.version > '3':
    PY3PLUS = True
else:
    PY3PLUS = False


def fix_object(value):
    """Fixes python objects so that they can be properly inserted into SQL queries"""
    if isinstance(value, set):
        value = ','.join(value)
    if PY3PLUS and isinstance(value, bytes):
        return value.decode('utf-8')
    elif not PY3PLUS and isinstance(value, unicode):
        return value.encode('utf-8')
    else:
        return value


def generate_sql_pattern(cols, row, tablename):
    values = list(map(fix_object, list(row)))
    values = list(values)
    real_value = []
    real_index = []
    for x in range(len(values) - 1):
        if values[x]:
            if isinstance(values[x], str) or isinstance(values[x], cx_Oracle.LOB):
                values[x] = str(values[x]).replace("'", "\\'")
            real_value.append(values[x])
            real_index.append(x)
    real_cols = []
    for a in real_index:
        real_cols.append(cols[a])

    template = 'INSERT INTO `{0}`.`{1}`({2}) VALUES ({3});'.format(
        'weixin', tablename,
        ', '.join(map(lambda key: '`%s`' % key, real_cols)),
        ', '.join(["'%s'"] * len(real_value))
    )
    return {'template': template, 'values': list(real_value)}


def concat_sql(cols, row, tablename):
    pattern = generate_sql_pattern(cols, row, tablename)
    sqltext = pattern['template'] % tuple(pattern['values'])
    return sqltext

