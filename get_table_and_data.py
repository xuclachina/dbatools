#!/usr/local/env python
# -*- coding: UTF-8 -*-

import cx_Oracle as cx
import os

from get_table_and_data_util import *



class Oralce_To_Mysql(object):
    def __init__(self, ip, port, username, passwd, tnsname):
        """初始化oracle连接"""
        try:
            dsn = cx.makedsn(ip, port, tnsname)
            self.conn = cx.connect(username, passwd, dsn)
        except cx.Error as e:
            print(e)
            exit(2)
        self.cursor = self.conn.cursor()

    def get_table_name(self):
        """获取shema下的表名"""
        self.cursor.execute('select table_name from user_tables')
        tables = self.cursor.fetchall()
        table_list = []
        if tables:
            for table in tables:
                table_list.append(table[0])
        return table_list

    def get_mysql_table_definition(self, table_list):
        """获取shema下所有表结构，Oracle转成MySQL"""
        f = open('C:/Users/xucl/Desktop/ddl/ddl.sql', 'a+', encoding='UTF-8', errors='ignore')
        for i in range(len(table_list) - 1):
            sql = """select dbms_lob.substr(fnc_table_to_mysql('dbname','%s','bigint','ID')) FROM DUAL""" % (table_list[i])
            self.cursor.execute(sql)
            t_table_definition_mysql = self.cursor.fetchone()
            s_table_definition_mysql = "".join(t_table_definition_mysql)
            mark = "#%s %s \n" % (i, table_list[i])
            f.write(mark)
            f.write(s_table_definition_mysql)
            f.write('\n')
        f.close()

    def get_mysql_table_data(self, table_list):
        """转储insert文件"""
        f = open('C:/Users/xucl/Desktop/ddl/dml.sql', 'a+', encoding='UTF-8', errors='ignore')
        for i in range(len(table_list) - 1):
            sql = """select * from %s where rownum<10""" % (table_list[i])
            #sql = """select * from ZJOL_ARTICLESTYLE where rownum < 5"""
            self.cursor.execute(sql)
            row = self.cursor.fetchall()
            for j in row:
                cols = [d[0] for d in self.cursor.description]
                sqltext = concat_sql(cols, j, table_list[i])
                f.write(sqltext)
                f.write('\n')
        f.close()

    def close_conn(self):
        self.conn.close()


if __name__ == '__main__':
    obj = Oralce_To_Mysql('127.0.0.1', 1521, 'username', 'password', 'sid')
    tablist = obj.get_table_name()
    obj.get_mysql_table_definition(tablist)
    obj.get_mysql_table_data(tablist)
    obj.close_conn()
