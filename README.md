# dbatools
存放日常工作所用到的运维工具

## dba_tools.zip
存放MySQL DBA常用软件如sysbench pt-tools等工具一键安装包

## check_mysql.py
MySQL数据库巡检脚本

##  compare_tools

最初做这个是由于我们内部从MariaDB迁移到官方版本MySQL5.7，为了比对两个版本的sql兼容性以及性能开发的小工具

- 抓取线上的sql放入txt文本，最好将dml也能转成select
- 配置源库目标库的配置，运行`sql_result_between_two_instance.py`
- 原理：抓取线上sql的1000条结果，对结果做checksum进行比较，如果结果一致返回True，否则返回False，并且输出两边的执行时间

