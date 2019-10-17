#!/bin/bash
DBIP='10.100.62.41'
DBPORT=3306
DBUSER='sbtest'
DBPASSWD='sbtest123456'
NOW=`date +'%Y%m%d%H%M'`
DBNAME="sbtest"
TBLCNT=25
WARMUP=120
DURING=900
ROWS=20000000
MAXREQ=20000000

# 并发压测的线程数，根据机器配置实际情况进行调整
RUN_NUMBER="8 16 32 64 96 128"

## prepare data
## sysbench /usr/local/share/sysbench/oltp_read_write.lua --mysql-host=localhost --mysql-port=3306 --mysql-user=root \
## --mysql-password=HNVl7Dbu5umbrlbt --mysql-socket=/tmp/mysql.sock --mysql-db=sbtest --tables=50 --table-size=20000000 --mysql_storage_engine=Innodb prepare

round=1
# 一般至少跑3轮测试，我正常都会跑10轮以上
while [ $round -lt 4 ]
do

rounddir=logs-round${round}
mkdir -p /tmp/${rounddir}

for thread in `echo "${RUN_NUMBER}"`
do

sysbench /usr/local/share/sysbench/oltp_read_write.lua --mysql-host=${DBIP} --mysql-port=${DBPORT} --mysql-user=${DBUSER} --mysql-password=${DBPASSWD} --mysql-db=${DBNAME} --tables=${TBLCNT} --table-size=${ROWS} --mysql_storage_engine=Innodb --threads=${thread} --time=${DURING} --report-interval=10 --rand-type=uniform run >> /tmp/${rounddir}/sbtest_${thread}.log

sleep 300
done

round=`expr $round + 1`
sleep 300
done
