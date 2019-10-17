#!/bin/env/ python
# coding:utf-8
import sys
import os

"""
读取/tmp目录下logs-round1文件夹
读取sbtest_x.log
获取TPS、QPS、95%rt
"""

for dirs in os.walk('/tmp'):
    if dirs[0].startswith('/tmp/logs-round'):
        round = dirs[0][10:]
        print('-------' + round + '-------')
        for file in dirs[2]:
            filename = dirs[0] + '/'+ file
            with open(filename,'r') as f:
                threads = file[7:][:-4]
                print('线程数' + threads)
                for line in f.readlines():
                    if 'transactions' in line:
                        tps_temp = line.strip('\n').strip('')
                        TPS = tps_temp.split()[2][1:]
                        print('TPS' + ' : '+ TPS)
                    elif 'queries:' in line:
                        qps_temp = line.strip('\n').strip('')
                        QPS = qps_temp.split()[2][1:]
                        print('QPS' + ' : '+ QPS)
                    elif '95th percentile' in line:
                        rt_temp = line.strip('\n').strip('')
                        rt = rt_temp.split()[2]
                        print('95%rt' + ' : '+ rt)