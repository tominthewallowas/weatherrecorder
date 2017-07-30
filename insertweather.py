#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Insert Weather checks for a trigger file, if it doesn't find one it shuts down.  If
it does find a trigger file it reads a file from a staging directory, opens a database
connection to a MySQL database, inserts one record of weather observations and
deletes the trigger file.
"""

 
# insertweather.py

import os, sys

import MySQLdb

from tombo.configfile import ConfigFile



configfile = ConfigFile('insertweather.conf')
runparams = configfile.getItems('Transfer')
databaseparams = configfile.getItems('Database')

def insertWeather():
	if not checkForTriggerFile():
		print 'no trigger'
		sys.exit(0)

	weather_data = collectWeatherData(runparams['weather_file'])

	db = getConnection()
	cur = db.cursor()
	
	if checkForDuplicate(cur, weather_data[0]):
		updateRecord(cur, weather_data)
	else:
		insertRecord(cur, weather_data)

	db.commit()

	removeFiles()

def checkForDuplicate(cur, date):
	sql = 'select Date from weather where Date="%s"' % date
	cur.execute(sql)
	return int(cur.rowcount)

def updateRecord(cur, weather_data):
	sql = 'update weather set Time="%s", Precip="%s", Comment="%s" where Date="%s"' % (weather_data[1], weather_data[2], weather_data[3], weather_data[0])
	result = cur.execute(sql)

def insertRecord(cur, weather_data):
	sql = 'insert into weather (Date, Time, Precip, Comment) values ("%s", "%s", %s, "%s")' % (weather_data[0], weather_data[1], weather_data[2], weather_data[3])
	result = cur.execute(sql)
	
def collectWeatherData(filename):
	with open(filename) as f:
		for line in f:
			weather_data = line
	return weather_data.split('|')

def getConnection():
	db = MySQLdb.connect(host=databaseparams['host'],
												user=databaseparams['user'],
												passwd=databaseparams['password'],
												db=databaseparams['database'])
	return db

def removeFiles():
	os.remove(runparams['trigger'])
	os.remove(runparams['weather_file'])

def checkForTriggerFile():
	return os.path.isfile(runparams['trigger'])

insertWeather()

