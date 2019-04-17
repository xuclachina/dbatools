# -*- coding: utf-8 -*-#

# -------------------------------------------------------------------------------
# Name:         snapshot
# Description:  
# Author:       xucl
# Date:         2019-04-17
# -------------------------------------------------------------------------------

import sys
import time
from utils import do_in_thread, command_line_args, mysql_variables, mysql_status, mysql_innodb_status,\
    mysql_slave_status, mysql_processlist, mysql_transactions, mysql_lock_info, mysql_error_log, mysql_slow_log, \
    system_disk_space, system_message, system_dmesg, system_top, system_iostat, system_mpstat, system_tcpdump, system_mem_info, \
    system_interrupts, system_ps, system_netstat, system_vmstat, get_mysql_status, get_mysql_innodb_status,\
    get_slave_status, get_system_status, check_conditions
from db_pool import DBAction

class Snapshot(object):
    def __init__(self, connection_settings, interval=None, conditions=None, storedir=None):
        if not conditions:
            raise ValueError('Lack of parameter: conditions')
        if not storedir:
            raise ValueError('Lack of parameter: storedir')
        self.conn_setting = connection_settings
        if not interval:
            self.interval = 10
        else:
            self.interval = interval
        self.conditions = conditions
        self.stordir = storedir


    def run(self):
        condition_dict = eval(self.conditions)
        dbaction = DBAction(conn_setting)
        while True:
            # mysql_status = get_mysql_innodb_status(dbaction)
            # mysql_innodb_status = get_mysql_innodb_status(dbaction)
            # mysql_slave_status = get_slave_status(dbaction)
            # mysql_system_status = get_system_status(dbaction)
            # collect_flag = check_conditions(mysql_status, mysql_innodb_status, mysql_slave_status, mysql_system_status, condition_dict)
            if 1==1:
                do_in_thread(mysql_status, dbaction)
            time.sleep(self.interval)

if __name__ == '__main__':
    args = command_line_args(sys.argv[1:])
    conn_setting = {'host': args.host, 'port': args.port, 'user': args.user, 'password': args.password, 'charset': 'utf8'}
    snapshot = Snapshot(connection_settings=conn_setting, interval=args.interval, conditions=args.conditions,
                        storedir=args.storedir)
    snapshot.run()


