#!/usr/bin/python
#coding: utf-8
#GRANT REPLICATION CLIENT ON *.* TO 'monitor'@'%' IDENTIFIED BY 'm0n1tor'; 

import sys
import getopt
import MySQLdb
import logging



dbhost=''
dbport=3306
dbuser="monitor"
dbpassword="m0n1tor"

#allow max Seconds_Behind_Master
MaxSBM=300

class Logger:
	Logger = None
	def __init__(self):
		fmt='%(asctime)s - %(filename)s:%(lineno)s - %(name)s - %(message)s'
def checkSlave():
	global dbhost
	global dbport
	global dbuser
	global dbpassword

	shortargs='h:P:'
	opts, args=getopt.getopt(sys.argv[1:],shortargs)
	for opt, value in opts:
		if opt=='-h':
			dbhost=value	
		elif opt=='-P':
			dbport=value
	#print "host : %s, port: %d, user: %s, password: %s" % (dbhost, int(dbport), dbuser, dbpassword)
	db = instanceMySQL(dbhost, dbport, dbuser, dbpassword)
	if ( db.connect() != 0 ):
		return 1
	slave_status=db.getSlave()
	return slave_status


class instanceMySQL:
	conn = None
	def __init__(self, host=None,port=None, user=None, passwd=None):
		self.dbhost= host
		self.dbport = int(port)
		self.dbuser = user
		self.dbpassword = passwd

			
	def connect(self):
	#	print "in db conn"
#		print "host : %s, port: %d, user: %s, password: %s" % (self.dbhost, self.dbport, self.dbuser, self.dbpassword)
		try:
			self.conn=MySQLdb.connect(host="%s"%self.dbhost, port=self.dbport,user="%s"%dbuser, passwd="%s"%self.dbpassword)
		except Exception, e:
#			print " Error"
			print e
			return 1
		return 0
	def getSlave(self):
		sql="show slave status"
		cursor = self.conn.cursor(cursorclass=MySQLdb.cursors.DictCursor)
		cursor.execute(sql)
		result = cursor.fetchall()
		row = result[0]
		if( row['Slave_IO_Running'] != 'Yes'):
			return 1
		if( row['Slave_SQL_Running'] != 'Yes'):
			return 1
		if ( row['Seconds_Behind_Master'] > MaxSBM):
			return 1
		cursor.close()
		self.disconnect()
		return 0

	
	def getWsrepState(self):
		sql="select VARIABLE_VALUE from information_schema.GLOBAL_STATUS where VARIABLE_NAME in ('WSREP_CLUSTER_STATUS', 'WSREP_LOCAL_STATE_COMMENT');"	
		cursor = self.conn.cursor()
		cursor.execute(sql)
		alldata = cursor.fetchall()
		if ( alldata[0][0] != 'Synced'):
			return 1
		if (alldata[1][0] !='Primary'):
			return 1
		return 0
		cursor.close()

	def disconnect(self):
		if (self.conn):
			self.conn.close()
			self.conn = None


if __name__== "__main__":
	st=checkSlave()
	#print st
	sys.exit(st)
