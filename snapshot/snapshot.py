# -*- coding: utf-8 -*-#

# -------------------------------------------------------------------------------
# Name:         snapshot
# Description:  
# Author:       xucl
# Date:         2019-04-17
# -------------------------------------------------------------------------------

from utils import *
from db_pool import DBAction
from threading import Lock

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
        
        while True:
            lock = Lock()
            global dbaction 
            dbaction = DBAction(self.conn_setting)
            status_dict1 = get_mysql_status(dbaction)
            sys_dict1 = get_sys_status()
            slow_log,error_log = get_log_dir(dbaction)
            slave_status_dict = get_slave_status(dbaction)

            time.sleep(1)

            status_dict2 = get_mysql_status(dbaction)
            sys_dict2 = get_sys_status()

            origin_status_list = ['Threads_connected', 'Threads_running', 'Innodb_row_lock_current_waits']
            origin_sys_status_list= ['cpu_user', 'cpu_sys', 'cpu_iowait']
            diff_status_list = ['Slow_queries', 'Innodb_buffer_pool_wait_free']
            diff_sys_status = ['sys_iops']

            origin_status_dict = get_origin_status(status_dict1, origin_status_list)
            origin_status_sys_dict = get_origin_sys_status(sys_dict1, origin_sys_status_list)
            diff_status_dict = get_diff_status(status_dict1, status_dict2, diff_status_list)
            diff_sys_status = get_sys_diff_status(sys_dict1, sys_dict2, diff_sys_status)

            check_dict = dict(origin_status_dict, **diff_status_dict, **origin_status_sys_dict, **diff_sys_status, **slave_status_dict)

            collect_flag = check_conditions(check_dict, condition_dict)

            time_now = datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
            filedir = create_unique_dir(self.stordir, time_now)
            if collect_flag:
                lock.acquire()
                thread_objs = []
                dbaction = DBAction(self.conn_setting)
                t1 = do_in_thread(mysql_variables, dbaction, filedir)
                thread_objs.append(t1)
                dbaction = DBAction(self.conn_setting)
                t2 = do_in_thread(mysql_status, dbaction, filedir)
                thread_objs.append(t2)
                dbaction = DBAction(self.conn_setting)
                t3 = do_in_thread(mysql_innodb_status, dbaction, filedir)
                thread_objs.append(t3)
                dbaction = DBAction(self.conn_setting)
                t4 = do_in_thread(mysql_slave_status, dbaction, filedir)
                thread_objs.append(t4)
                dbaction = DBAction(self.conn_setting)
                t5 = do_in_thread(mysql_processlist, dbaction, filedir)
                thread_objs.append(t5)
                dbaction = DBAction(self.conn_setting)
                t6 = do_in_thread(mysql_transactions, dbaction, filedir)
                thread_objs.append(t6)
                dbaction = DBAction(self.conn_setting)
                t7 = do_in_thread(mysql_lock_info, dbaction, filedir)
                thread_objs.append(t7)
                t8 = do_in_thread(mysql_error_log, slow_log, filedir)
                thread_objs.append(t8)
                t9 = do_in_thread(mysql_slow_log, error_log, filedir)
                thread_objs.append(t9)
                t10 = do_in_thread(system_message, '/var/log/messages', filedir)
                thread_objs.append(t10)
                t11 = do_in_thread(system_dmesg, '/var/log/dmesg', filedir)
                thread_objs.append(t11)
                t12 = do_in_thread(system_top, filedir)
                thread_objs.append(t12)
                t13 = do_in_thread(system_iostat, filedir)
                thread_objs.append(t13)
                t14 = do_in_thread(system_mpstat, filedir)
                thread_objs.append(t14)
                t15 = do_in_thread(system_tcpdump, filedir)
                thread_objs.append(t15)
                t16 = do_in_thread(system_mem_info, filedir)
                thread_objs.append(t16)
                t17 = do_in_thread(system_interrupts, filedir)
                thread_objs.append(t17)
                t18 = do_in_thread(system_ps, filedir)
                thread_objs.append(t18)
                t19 = do_in_thread(system_netstat, filedir)
                thread_objs.append(t19)
                t20 = do_in_thread(system_vmstat, filedir)
                thread_objs.append(t20)
                for thread_obj in thread_objs:
                    thread_obj.join()
                
            lock.release()
            
            time.sleep(self.interval)


if __name__ == '__main__':
    args = command_line_args(sys.argv[1:])
    conn_setting = {'host': args.host, 'port': args.port, 'user': args.user, 'password': args.password, 'charset': 'utf8'}
    snapshot = Snapshot(connection_settings=conn_setting, interval=args.interval, conditions=args.conditions,
                        storedir=args.storedir)
    snapshot.run()
