#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   test.py
@Time    :   2020/05/18 20:57:15
@Author  :   xuchenliang 
@Version :   1.0
@Desc    :   None
'''

# here put the import lib
import os
import sys
import pymysql
import subprocess


class MySQLApi(object):
    def __init__(self, host=None, port=None, user=None, password=None, db=None):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.db = db
        self._cnx = None

    def _local_cnx(self):
        cnx = pymysql.connect(host=self.host,
                              port=self.port,
                              user=self.user,
                              passwd=self.password,
                              db=self.db,
                              max_allowed_packet=1024 * 1024 * 1024,
                              charset='utf8',
                              cursorclass=pymysql.cursors.DictCursor)
        # 设置最大查询时间60s
        cnx._read_timeout = 60
        self._cnx = cnx

    def _close(self):
        self._cnx.close()

    def _execute(self, sql):
        self._local_cnx()
        cursor = self._cnx.cursor()
        try:
            cursor.execute(sql)
            result = cursor.fetchall()
            return result
        except Exception as err:
            print(err)
            return
        finally:
            self._close()
    
    def _print_result(self, result):
        """
        @result 字典形式
        """
        for item in result:
            print((', ').join(["{}: {}".format(key, item[key]) for key in item.keys()]))
                
    def _get_database(self):
        """
        @action: get all database name
        @params: none
        @return: list
        """
        sql = "SELECT schema_name as schema_name FROM information_schema.SCHEMATA  WHERE schema_name NOT IN('information_schema','mysql','performance_schema','undolog', 'sys')"
        result = self._execute(sql)
        databases = []
        if not result:
            return databases
        for db in result:
            databases.append(db['schema_name'])

        return databases

    def _get_tables(self, dbname):
        """
        @action: get all tables in specified database
        @params: dbname->database name
        @return: list
        """
        sql = "SELECT table_name as table_name FROM information_schema.tables WHERE table_schema = '{}'".format(dbname)
        result = self._execute(sql)
        tables = []
        if not result:
            return tables
        for db in result:
            tables.append(db['table_name'])
            
        return tables

    def _get_variable(self, variable):
        """
        @action: get specified global variable
        @params: variable->variable name
        @return: dict
        """
        self._local_cnx()
        cursor = self._cnx.cursor()
        cursor.execute("show global variables like '{}';".format(variable))
        result = cursor.fetchone()
        if not result:
            return {}
        self._close()
        return {result['Variable_name']:result['Value']}

    def _get_file_size(self, dir, dbname, tablename):
        """
        @action: get table idb size in os
        @params: dir->datadir
                 dbname->database name
                 tablename-> table name
        @return: int
        """
        tableibd = "{}{}/{}.ibd".format(dir, dbname, tablename)
        try:
            size = os.path.getsize(tableibd)
            return size
        except Exception as err:
            print(err)
            return 0

    def _get_version(self):
        """
        @action: get mysql version
        @params: none
        @return: dict
        """
        return self._execute('select @@version as version')

    def query(self, sql):
        thread_id = self._cnx.thread_id()
        result = self._execute(sql)
        print(thread_id)
        print(result)

    def kill(self, sql_pattern):
        """
        @action: kill slow querys
        @params: sql_pattern->the begging part of slow query
        @return: none
        """
        sql = "SELECT id FROM INFORMATION_SCHEMA.PROCESSLIST WHERE info LIKE '{}%'".format(sql_pattern)
        result = self._execute(sql)
        if not result:
            print('未匹配到会话')

        for thread in result:
            result = self._execute('kill {}'.format(int(thread['id'])))
            print('kill {} success'.format(int(thread['id'])))

    def export(self, dir):
        """
        @action: export all table structure
        @params: dir->export data to this base directory
        @return: none
        """
        basedir = "{}/{}".format(dir, self.host)
        if not os.path.exists(basedir):
            os.makedirs(basedir)

        databases = self._get_database()

        if databases:
            for db in databases:
                p=subprocess.Popen("mysqldump -h{} -u{} -p{} -d {} > {}/{}.sql".format(self.host, self.user, self.password, db, basedir, db),
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT)
                code = p.wait()
                if code:
                    print("{db}库导出失败".format(db=db))
                else:
                    print("{db}库导出成功".format(db=db))
            print("导出结束")

    def onlineddl(self, db, table, action):
        """
        @action: online ddl using pt-osc
        @params: db->database name
                 table->table name
                 action->ddl,for example:add column c1 varchar(10)
        @return: none
        """
        databases = self._get_database()
        if db not in databases:
            print("db不存在")
            sys.exit(1)
        oscmd = """
            pt-online-schema-change --host={} -u {} -p {} \
            --alter="{}" \
            --charset=utf8 \
            --chunk-size=5000 \
            --print \
            --no-version-check \
            --execute \
            --no-check-replication-filters \
            --recursion-method=none D={},t={}""".format(self.host, self.user, self.password, action, db, table)

        result = subprocess.run(oscmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if result.returncode == 0:
            msg = str(result.stdout, encoding="utf-8").split('\n')
            for line in msg:
                print(line)

    def _check_fragment(self):
        databases = self._get_database()
        if not databases:
            return 
        datadir = self._get_variable('datadir')
        self._local_cnx()
        cursor = self._cnx.cursor()
        result = []
        for db in databases:
            dbdict = dict()
            tables = self._get_tables(db)
            if not tables:
                continue
            for table in tables:
                cursor.execute("SELECT table_rows*avg_row_length as size FROM information_schema.tables WHERE table_schema= '{}' AND table_name = '{}';".format(db, table))
                dbsize = cursor.fetchone() 
                osize = self._get_file_size(datadir['datadir'], db, table)
                fragment_pct = round((1 - int(dbsize['size'])/int(osize))*100, 2)
                if fragment_pct > 50:
                    dbdict['db'] = db
                    dbdict['tbl'] = table
                    dbdict['pct'] = fragment_pct
                    result.append(dbdict)
        return result

    def _check_no_primary(self):
        sql = """SELECT a.TABLE_SCHEMA as `db`, a.TABLE_NAME as `tbl` FROM ( SELECT TABLE_SCHEMA, TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA NOT IN ( 'mysql', 'sys', 'information_schema', 'performance_schema' ) AND  TABLE_TYPE = 'BASE TABLE' ) AS a LEFT JOIN ( SELECT TABLE_SCHEMA, TABLE_NAME FROM information_schema.TABLE_CONSTRAINTS WHERE CONSTRAINT_TYPE = 'PRIMARY KEY' ) AS b ON a.TABLE_SCHEMA = b.TABLE_SCHEMA AND a.TABLE_NAME = b.TABLE_NAME WHERE b.TABLE_NAME IS NULL"""
        tables = self._execute(sql)

        return tables

    def _check_sub_index(self):
        sql = """SELECT TABLE_SCHEMA, TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX, COLUMN_NAME, CARDINALITY, SUB_PART FROM INFORMATION_SCHEMA.STATISTICS WHERE  SUB_PART > 10 ORDER BY SUB_PART DESC"""
        results = self._execute(sql)

        return results

    def _check_long_index(self):
        sql = """select c.table_schema as `db`, c.table_name as `tbl`,   c.COLUMN_NAME as `col`, c.DATA_TYPE as `col_type`,   c.CHARACTER_MAXIMUM_LENGTH as `col_len`,   c.CHARACTER_OCTET_LENGTH as `col_len_bytes`,    s.NON_UNIQUE as `isuniq`, s.INDEX_NAME, s.CARDINALITY,   s.SUB_PART, s.NULLABLE   from information_schema.COLUMNS c inner join information_schema.STATISTICS s   using(table_schema, table_name, COLUMN_NAME) where   c.table_schema not in ('mysql', 'sys', 'performance_schema', 'information_schema', 'test') and   c.DATA_TYPE in ('varchar', 'char', 'text', 'blob') and   ((CHARACTER_OCTET_LENGTH > 50 and SUB_PART is null) or   SUB_PART * CHARACTER_OCTET_LENGTH/CHARACTER_MAXIMUM_LENGTH >50)"""
        results = self._execute(sql)

        return results

    def _check_uncomit_trans(self):
        sql = """select b.host, b.user, b.db, b.time, b.COMMAND, a.trx_id, a. trx_state from information_schema.innodb_trx a left join information_schema.PROCESSLIST b on a.trx_mysql_thread_id = b.id"""
        results = self._execute(sql)

        return results

    def _check_lock_waits(self):
        version = self._get_version()
        if version[0]['version'].startswith('5.7'):
            sql = """SELECT lw.requesting_trx_id AS request_XID,   trx.trx_mysql_thread_id as request_mysql_PID,  trx.trx_query AS request_query,   lw.blocking_trx_id AS blocking_XID,   trx1.trx_mysql_thread_id as blocking_mysql_PID,  trx1.trx_query AS blocking_query, lo.lock_index AS lock_index FROM   information_schema.innodb_lock_waits lw INNER JOIN   information_schema.innodb_locks lo   ON lw.requesting_trx_id = lo.lock_trx_id INNER JOIN   information_schema.innodb_locks lo1   ON lw.blocking_trx_id = lo1.lock_trx_id INNER JOIN   information_schema.innodb_trx trx   ON lo.lock_trx_id = trx.trx_id INNER JOIN   information_schema.innodb_trx trx1   ON lo1.lock_trx_id = trx1.trx_id"""
        elif version[0]['version'].startswith('8.0'):
            sql = """SELECT  t1.REQUESTING_ENGINE_TRANSACTION_ID  AS request_XID, t1.REQUESTING_THREAD_ID AS request_mysql_PID, t2.trx_query AS request_query, t1.BLOCKING_ENGINE_TRANSACTION_ID AS blocking_XID, t1.BLOCKING_THREAD_ID AS blocking_mysql_PID, t3.trx_query AS blocking_query, t4.INDEX_NAME AS lock_index, t4.LOCK_MODE  AS lock_mode, t4.LOCK_STATUS AS lock_status, t4.LOCK_DATA AS lock_data FROM performance_schema.data_lock_waits t1  INNER JOIN information_schema.innodb_trx t2 ON t1.REQUESTING_ENGINE_TRANSACTION_ID=t2.trx_id INNER JOIN information_schema.innodb_trx t3 ON t1.BLOCKING_ENGINE_TRANSACTION_ID=t3.trx_id INNER JOIN performance_schema.data_locks t4    ON t1.REQUESTING_ENGINE_LOCK_ID=t4.ENGINE_LOCK_ID;"""
        results = self._execute(sql)
        
        return results

    def check(self):
        """
        检查包括：
        1.无主键表
        返回示例：{'db': 'xucl', 'tbl': 't2'}
        
        2.部分索引
        返回示例：{'TABLE_SCHEMA': 'xucl', 'TABLE_NAME': 't2', 'INDEX_NAME': 'idx_c1_part', 'SEQ_IN_INDEX': 1, 'COLUMN_NAME': 'c1', 'CARDINALITY': 0, 'SUB_PART': 100}

        3.索引长度过长的表
        返回示例：{'db': 'xucl', 'tbl': 't2', 'col': 'c1', 'col_type': 'varchar', 'col_len': 1000, 'col_len_bytes': 4000, 'isuniq': 1, 'INDEX_NAME': 'idx_c1_part', 'CARDINALITY': 0, 'SUB_PART': 100, 'NULLABLE': ''}
        
        4.未完成事务
        返回示例：{'host': 'localhost', 'user': 'root', 'db': 'xucl', 'time': 13, 'COMMAND': 'Sleep', 'trx_id': '5831', 'trx_state': 'RUNNING'}
        
        5.行锁等待事件
        返回示例：{'request_XID': 5849, 'request_mysql_PID': 2027, 'request_query': 'delete from t1', 'blocking_XID': 5843, 'blocking_mysql_PID': 2018, 'blocking_query': None, 'lock_index': 'PRIMARY', 'lock_mode': 'X,REC_NOT_GAP', 'lock_status': 'WAITING', 'lock_data': '1'}

        6.碎片率检查
        返回示例：{'db': 'xucl', 'tbl': 't2', 'pct': 100.0}
        """
        print("-------1.检查无主键表-------")
        self._print_result(self._check_no_primary())
        print("-------2.检查部分索引表-------")
        self._print_result(self._check_sub_index())
        print("-------3.检查索引长度过长的表-------")
        self._print_result(self._check_long_index())
        print("-------4.检查未完成事务-------")
        self._print_result(self._check_uncomit_trans())
        print("-------5.检查行锁等待事件-------")
        self._print_result(self._check_lock_waits())
        print("-------6.检查表碎片率-------")
        self._print_result(self._check_fragment())

    def main(self):
        """
        使用示例：
        1.kill 慢查：self.kill('select SLEEP')
        2.巡检：self.check()
        3.pt-osc执行DDL：self.onlineddl('xucl', 't1', 'add c1 varchar(10)')
        4.导出所有业务库表结构：self.export()
        5.执行查询，并返回线程id：self.query('select * from t1;')
        """
        self.check()

if __name__ == "__main__":
    rds = MySQLApi(host='127.0.0.1', port=3306, user='root', password='123456', db='xucl')
    rds.main()