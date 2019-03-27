#!/usr/bin/python
#coding: utf-8
# grant usage on *.* to 'pxc-monitor'@'%' identified by 'showpxc';  

import sys
import getopt
import MySQLdb
import logging



dbhost=''
dbport=3306
dbuser="pxc-monitor"
dbpassword="showpxc"

#DEBUG, INFO, WARNING, ERROR, CRITICAL
log_level="CRITICAL"
log_file="/var/log/checkPxc.log"

class Logger:
	Logger = None
	def __init__(self):
		fmt='%(asctime)s - %(filename)s:%(lineno)s - %(name)s - %(message)s'
def checkPxc():
	global dbhost
	global dbport
	global dbuser
	global dbpassword

	shortargs='h:p:'
	opts, args=getopt.getopt(sys.argv[1:],shortargs)
	for opt, value in opts:
		if opt=='-h':
			dbhost=value	
		elif opt=='-p':
			dbport=value
	#print "host : %s, port: %d, user: %s, password: %s" % (dbhost, int(dbport), dbuser, dbpassword)
	db = instancePxc(dbhost, dbport, dbuser, dbpassword)
	if ( db.connect() != 0 ):
		return 1
	pxc_status=db.getWsrepState()
	db.disconnect()
	return pxc_status


class instancePxc:
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
	st=checkPxc()
	#print st
	sys.exit(st)
