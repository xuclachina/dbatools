# coding:gbk

import time
import threading
import getpass
import argparse
import sys


class FuncThread(threading.Thread):

    def __init__(self, func, *args, **kwargs):
        super(FuncThread, self).__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.finished = False
        self.result = None

    def run(self):
        self.result = self.func(*self.args, **self.kwargs)
        self.finished = True

    def is_finished(self):
        return self.finished

    def get_result(self):
        return self.result


def do_in_thread(func, *args, **kwargs):
    ft = FuncThread(func, *args, **kwargs)
    ft.start()
    return ft


def handle_timeout(func, timeout, *args, **kwargs):
    interval = 1

    ret = None
    while timeout > 0:
        begin_time = time.time()
        ret = func(*args, **kwargs)
        if ret:
            break
        time.sleep(interval)
        timeout -= time.time() - begin_time

    return ret


def create_unique_dir(dirname, snaptime):
    result_dir = dirname + '/' + snaptime
    # if filedir is not exist than create
    if not os.path.exists(result_file):
        os.mkdir(result_dir)
    return result_dir


def parse_args():
    """parse args for snapshot"""

    parser = argparse.ArgumentParser(description='Snapshot your Database and Server', add_help=False)
    connect_setting = parser.add_argument_group('connect setting')
    connect_setting.add_argument('-h', '--host', dest='host', type=str,
                                 help='Host the MySQL database server located', default='127.0.0.1')
    connect_setting.add_argument('-u', '--user', dest='user', type=str,
                                 help='MySQL Username to log in as', default='root')
    connect_setting.add_argument('-p', '--password', dest='password', type=str, nargs='*',
                                 help='MySQL Password to use', default='')
    connect_setting.add_argument('-P', '--port', dest='port', type=int,
                                 help='MySQL port to use', default=3306)

    parser.add_argument('--interval', dest='interval', type=int, default=10,
                        help="interval time to check snapshot condition")
    parser.add_argument('--help', dest='help', action='store_true', help='help information', default=False)
    parser.add_argument('--conditions', dest='conditions', default=False,
                        help="Specify trigger conditions")
    parser.add_argument('--storedir', dest='storedir', default=False,
                        help="Specify datadir to store snapshot files")
    return parser


def command_line_args(args):
    need_print_help = False if args else True
    parser = parse_args()
    args = parser.parse_args(args)
    if args.help or need_print_help:
        parser.print_help()
        sys.exit(1)
    if not args.conditions:
        raise ValueError('Lack of parameter: conditions')
    if not args.storedir:
        raise ValueError('Lack of parameter: storedir')
    if not args.password:
        args.password = getpass.getpass()
    else:
        args.password = args.password[0]
    return args


def mysql_variables():
    pass


def mysql_status(dbaction):
    sql = 'show global status'
    status_obj = dbaction.data_inquiry(sql)
    print(status_obj)


def mysql_innodb_status():
    pass


def mysql_slave_status():
    pass


def mysql_processlist():
    pass


def mysql_transactions():
    pass


def mysql_lock_info():
    pass


def mysql_error_log():
    pass


def mysql_slow_log():
    pass


def system_disk_space():
    pass


def system_message():
    pass


def system_dmesg():
    pass


def system_top():
    pass


def system_iostat():
    pass


def system_mpstat():
    pass


def system_tcpdump():
    pass


def system_mem_info():
    pass


def system_interrupts():
    pass


def system_ps():
    pass


def system_netstat():
    pass


def system_vmstat():
    pass


def check_conditions(mysql_status, mysql_innodb_status, mysql_slave_status, mysql_system_status, condition_dict):
    pass


def get_mysql_status(dbaction):
    sql = 'show global status'
    status_obj = dbaction.data_inquiry(sql)
    print(status_obj)


def get_mysql_innodb_status(dbaction):
    return {}


def get_system_status(dbaction):
    return {}


def get_slave_status(dbaction):
    return {}