#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Weather Recorder collects daily weather data for storage
in a database and posting to a web site.
"""
 
# weatherrecorderwx.py

import wx
import os, sys
from datetime import date

from wx.lib.masked import Ctrl
from wx.lib.masked import NumCtrl
from ObjectListView import ObjectListView
from ObjectListView import FastObjectListView, ColumnDefn, EVT_CELL_EDIT_FINISHED, EVT_CELL_EDIT_STARTING

from tombo.sqlitedb import SQLiteDB
from tombo.securework import SecureWork
from tombo.configfile import ConfigFile
from tombo.timedstatusbar import TimedStatusBar

# Message Indexes
PRIMARY_KEY = 0
EDIT_CANCELLED = 1
CHOOSE_MONTHYEAR = 2
CHOOSE_YEAR = 3
SELECT_ROW = 4

# Message Severity
ADVISORY = 0
WARNING = 1
SEVERE = 2

months = {'01':'Jan', '02':'Feb', '03':'Mar', '04':'Apr', '05':'May', '06':'Jun', '07':'Jul', '08':'Aug', '09':'Sep', '10':'Oct', '11':'Nov', '12':'Dec',}

messages = [
	("You can't change a primary key.", WARNING), 
	("Edit cancelled by user.", ADVISORY),
	("Please choose a year or a year and a month.", ADVISORY),
	("You have chosen a month - you must also choose a year.", ADVISORY),
	("In order to delete a row you have to select a row.", WARNING), 
	]

class MainWindow(wx.Frame):
	""" A frame that encloses a panel which encloses widgets. """
	def __init__(self, parent, title):
		""" Use the constructor to build the interface and show the window. """
		super(MainWindow, self).__init__(parent, title=title, size=(650, 400))
		self.gatherConfigInfo('weatherrecorderwx.conf')
		self.widgetids = {}
		self.InitUI()
		self.Centre()
		self.Show()

	def gatherConfigInfo(self, configfile):
		config = ConfigFile(configfile)
		self.host = config.getItems('Host')
		self.transfer = config.getItems('Transfer')
		self.years = config.getItems('Years Selection')['years'].split(',')
		self.timerinterval = config.getNumber('Status Bar', 'interval')
		self.db = SQLiteDB(db_type=config.getItem('Database', 'file'))
		self.tablename = config.getItem('Database', 'tablename')
		self.insertstatement = config.getItem('Database', 'insertstatement')
		self.primarykey = config.getItem('Database', 'primarykey')
		self.primarykeyindex = config.getNumber('Database', 'primarykeyindex')

	def InitUI(self):
		""" Organizes building the interface. """
		# Top level panel - holds all other windows
		vbox1 = wx.BoxSizer(wx.VERTICAL)
		panel = wx.Panel(self)
		vbox1.Add(item=panel, proportion=1, flag=wx.ALL|wx.EXPAND)
		self.SetSizer(vbox1)
		vbox2 = wx.BoxSizer(wx.VERTICAL)
		panel.SetSizer(vbox2)
		vbox2.Add(item=self.buildEntryGrid(panel), flag=wx.EXPAND | wx.ALL, border=10)
		vbox2.Add(item=self.buildAddButtonBox(panel), flag=wx.CENTER)
		vbox2.Add(item=self.buildWeatherList(panel), proportion=1, flag=wx.EXPAND | wx.ALL, border=10)
		vbox2.Add(item=self.buildFilterBox(panel, self.years), flag=wx.CENTER | wx.BOTTOM, border=10)
		self.buildStatusBar()
		self.populateList(self.selectData(self.buildSelectStatement(year=None, month=None)))
		self.tcDate.SetFocus()

	# Create the visual elements
	def buildEntryGrid(self, parent):
		entrygrid = wx.FlexGridSizer(rows=2, cols=4, hgap=3, vgap=3)
		entrygrid.AddGrowableCol(3)
		entrygrid.AddMany(self.buildFields(parent))
		return entrygrid

	def buildAddButtonBox(self, parent):
		hbox = wx.BoxSizer(wx.HORIZONTAL)
		labels = ['&Add', '&Send to Web', '&Quit', '&Delete']
		for label in labels:
			button = wx.Button(parent=parent, label=label)
			button.Bind(wx.EVT_BUTTON, self.onButtonClick, id=button.GetId())
			self.widgetids[button.GetId()] = label
			hbox.Add(button)
		return hbox
    
	def buildWeatherList(self, parent):
		self.weatherlist = FastObjectListView(parent=parent, id=wx.ID_ANY, style=wx.LC_REPORT|wx.SUNKEN_BORDER)
		self.weatherlist.Bind(EVT_CELL_EDIT_STARTING, self.HandleCellEditStarting)
		self.weatherlist.Bind(EVT_CELL_EDIT_FINISHED, self.HandleCellEditFinished)
		self.weatherlist.cellEditMode = ObjectListView.CELLEDIT_DOUBLECLICK
		return self.weatherlist

	def buildFilterBox(self, parent, years):
		hbox = wx.BoxSizer(wx.HORIZONTAL)
		self.cboYear = wx.ComboBox(parent=parent, id=wx.ID_ANY, value='Year', pos=(15, 30), size=(100, -1), choices=years, style=wx.CB_DROPDOWN)
		months = ['01','02','03','04','05','06','07','08','09','10','11','12']
		self.cboMonth = wx.ComboBox(parent=parent, id=wx.ID_ANY, value='Month', pos=(15, 30), size=(100, -1), choices=months, style=wx.CB_DROPDOWN)
		btnApplyFilter = wx.Button(parent=parent, label='A&pply Filter')
		btnApplyFilter.Bind(wx.EVT_BUTTON, self.filterButtonClick, id=btnApplyFilter.GetId())
		btnClearFilter = wx.Button(parent=parent, label='C&lear Filter')
		btnClearFilter.Bind(wx.EVT_BUTTON, self.filterButtonClick, id=btnClearFilter.GetId())
		hbox.Add(self.cboYear, flag=wx.RIGHT, border=20)
		hbox.Add(self.cboMonth, flag=wx.RIGHT, border=20)
		hbox.Add(btnApplyFilter, flag=wx.RIGHT, border=20)
		hbox.Add(btnClearFilter, flag=wx.RIGHT, border=20)
		return hbox

	def buildStatusBar(self):
		""" Build a lowly status bar. """
		self.timedstatusbar = TimedStatusBar(self, includetimer=True, interval=self.timerinterval)
		self.SetStatusBar(self.timedstatusbar)
		self.timedstatusbar.message='The Weather Recorder is ready to record!'

	def buildFields(self, panel):
		""" Sets up a list of tuples that will be returned to the AddMany method of a grid. """
		self.tcDate = self.buildMaskedControl(panel, value=wx.DateTime_Now().Format("%m/%d/%Y"))
		self.tcTime = self.buildMaskedControl(panel, format='TIMEHHMM', value=wx.DateTime_Now().Format("%I:%M %p"))
		self.tcMeasurement = self.buildMaskedNumber(panel, value=0.00)
		self.tcComment = wx.TextCtrl(panel, id=wx.ID_ANY, style=wx.EXPAND)
		return [
			(wx.StaticText(panel, id=wx.ID_ANY, label='Date'), 0),
			(wx.StaticText(panel, id=wx.ID_ANY, label='Time'), 0),
			(wx.StaticText(panel, id=wx.ID_ANY, label='Measurement'), 0),
			(wx.StaticText(panel, id=wx.ID_ANY, label='Comment'), 0),
			(self.tcDate, 0),
			(self.tcTime, 0),
			(self.tcMeasurement, 0),
			(self.tcComment, 0, wx.EXPAND)
			]

	def buildMaskedControl(self, owner, value=None, format='USDATEMMDDYYYY/', size=(-1, -1)):
		return Ctrl(owner, value=value, style= wx.TE_PROCESS_ENTER, autoformat=format, size=size)
    
	def buildMaskedNumber(self, owner, value=None, format=(1,2), size=(-1, -1)):
			return NumCtrl(owner, value = 0, integerWidth = format[0], fractionWidth = format[1],
				allowNegative = False, autoSize = False, size=size)

	# Methods related to a button click
	def onButtonClick(self, event):
		eventid = event.GetId()
		if self.widgetids[eventid] == '&Add':
			self.insertRecord()
		elif self.widgetids[eventid] == '&Send to Web':
			self.stageWeatherObservation()
			self.stageHTMLTransfer()
		elif self.widgetids[eventid] == '&Quit':
			self.Close()
		elif self.widgetids[eventid] == '&Delete':
			self.deleteRecord()
		else: print 'Error'

	def filterButtonClick(self, event):
		widgetlabel = event.GetEventObject().GetLabel()
		if widgetlabel == 'A&pply Filter':
			year = self.cboYear.GetValue()
			month = self.cboMonth.GetValue()
			if year == 'Year' and month == 'Month':
				# No year or month selected - error
				self.setMessage(messages[CHOOSE_MONTHYEAR])
			elif year == 'Year' and month != 'Month':
				# No year but month selected - error
				self.setMessage(messages[CHOOSE_YEAR])
			elif year != 'Year' and month == 'Month':
				# Year selected and no month - select entire year
				self.populateList(self.selectData(self.buildSelectStatement(year, month=None)))
			else:
				# Year and month selected - select year and month
				self.populateList(self.selectData(self.buildSelectStatement(year, month)))

		if widgetlabel == 'C&lear Filter':
			self.cboYear.SetValue('Year')
			self.cboMonth.SetValue('Month')
			self.populateList(self.selectData(self.buildSelectStatement(year=None, month=None)))

	#Methods that handle SQL
	def buildSelectStatement(self, year=None, month=None):
		if year and not month:
			statement = 'select Key, Date, Time, Precip, Comment from weather where Date between %s and %s order by Date desc' % (year+'0101', year+'1231')
		elif year and month:
			statement = 'select Key, Date, Time, Precip, Comment from weather where Date between %s and %s order by Date desc' % (year+month+'01', year+month+'31')
		else:
			statement = 'select Key, Date, Time, Precip, Comment from weather order by Date desc'
		return statement

	def insertRecord(self):
		weatherdata = self.prepareWeatherData()
		#date = self.tcDate.GetValue().split('/')
		#reformatted = date[2] + date[0] + date[1]
		#data = [(reformatted, self.tcTime.GetValue(), self.tcMeasurement.GetValue(), self.tcComment.GetValue())]
		#print(weatherdata)
		self.db.insertData(self.insertstatement, weatherdata)
		self.populateList(self.selectData(self.buildSelectStatement(year=None, month=None)))
    
	def deleteRecord(self):
		rowindex = self.weatherlist.GetFocusedRow()
		mo = self.weatherlist.GetObjectAt(rowindex)
		if not self.weatherlist.IsObjectSelected(mo):
			self.setMessage(messages[SELECT_ROW])
			return
		dlg = wx.MessageDialog(parent=None,
			message="If you click 'Yes' then the row selected\nwill be deleted. Click 'Cancel'\nto stop delete.",
			caption='Delete Warning!',
			style=wx.YES_NO | wx.ICON_EXCLAMATION | wx.CANCEL)
		retCode = dlg.ShowModal()
		if retCode != wx.ID_YES:
			return
		dlg.Destroy()
		delete_statememt = "delete from %s where %s = ?" % (self.tablename, self.primarykey) 
		self.db.updateData(delete_statememt, (mo[0],))
		self.populateList(self.selectData(self.buildSelectStatement(year=None, month=None)))

	def selectData(self, statement):
		weatherdata = self.db.select(statement)
		return [list(x) for x in weatherdata]

	def prepareWeatherData(self):
		date = self.tcDate.GetValue().split('/')
		reformatted_date = date[2] + date[0] + date[1]
		return [(reformatted_date, self.tcTime.GetValue(), self.tcMeasurement.GetValue(), self.tcComment.GetValue())]

	# Methods for creating and sending HTML to the web
	def stageWeatherObservation(self):
		weather_data = self.prepareWeatherData()
		self.createWeatherFile(weather_data)

	def createWeatherFile(self, weather_data):
		weather_for_file = weather_data[0][0] + '|' + weather_data[0][1] + '|' + str(weather_data[0][2]) + '|' + weather_data[0][3]
		weatherfile = open(self.transfer['source'] + self.transfer['weatherfile'], 'w')
		weatherfile.write(weather_for_file)
		weatherfile.close()
		

	def stageHTMLTransfer(self):
		html = self.buildWeatherHTML()
		self.createIncludeFile(html, self.transfer['source'] + self.transfer['includefile'])
		self.sendToWeb(self.host, self.transfer)

	def buildWeatherHTML(self):
		date_parms = self.gatherDateParms()
		daily_statement =  "select substr(Date, 5,2) || '/' || substr(Date, 7, 2) || '/' || substr(Date, 1, 4), Time, Precip, Comment from weather order by Date desc limit 10"
		monthly_statement = "select substr(Date, 5, 2) as Month, sum(Precip) as Precip from weather where substr(Date, 1, 4) = '%s' group by Month order by Month desc" % (date_parms['year'])
		yearly_statement = "select sum(Precip) as Precip from weather where substr(Date, 1, 4) = '%s'" % (date_parms['year'])

		daily_data = self.selectData(daily_statement)
		monthly_data = self.selectData(monthly_statement)
		yearly_data = self.selectData(yearly_statement)

		# Daily Observations Table
		applyalt = False
		html = []
		html.append('<h2>Daily Weather Observations</h2>')
		html.append('<table id="weatherobs"><tr><th>Date</th><th>Time</th><th>Precipitation</th><th>Comment</th></tr>')
		for row in daily_data:
			if applyalt:
				html.append('<tr class="alt">')
				applyalt = False
			else:
				html.append('<tr>')
				applyalt = True
			a, b, c, d = row
			html.append('<td>{}</td><td>{}</td><td>{:0.2f}</td><td>{}</td>'.format(a, b, c, d))
			html.append('</tr>')
		html.append('</table>')

		# Monthly Precipitation Totals
		applyalt = False
		html.append('<br/><h2>Monthly Precipitation</h2>')
		html.append('<table id="weatherobs"><tr><th>Month</th><th>Precipitation</th></tr>')
		for row in monthly_data:
			if applyalt:
				html.append('<tr class="alt">')
				applyalt = False
			else:
				html.append('<tr>')
				applyalt = True
			for i, element in enumerate(row, start=0):
				html.append('<td>' + (months[element] if i == 0 else '{:0.2f}'.format(element) + '</td>'))
			html.append('</tr>')
		html.append('<tr><td>Year To Date</td><td>{:0.2f}</td></tr>'.format(yearly_data[0][0]))
		html.append('</table>')
		return ''.join(html)

	def createIncludeFile(self, html, includefile):
		includefile = open(includefile, 'w')
		includefile.write(html)
		includefile.close()

	def sendToWeb(self, host, transfer):
		sw = SecureWork(host=host['host'], username=host['username'], password=host['password'])
		#sw.ftp_put([transfer['includefile']], transfer['source'], transfer['destination'])
		sw.ftp_put([transfer['weatherfile']], transfer['source'], transfer['destination'])
		sw.command(transfer['command'])

	def gatherDateParms(self):
		d = date.today()
		return {'month':str(d.month).zfill(2), 'year':str(d.year)}

	# Methods related to the Object List View
	def populateList(self, data):
		self.weatherlist.SetObjects(list())
		cd = [
			ColumnDefn(title='Key', valueGetter=0, minimumWidth=50, width=50),
			ColumnDefn(title='Date', valueGetter=1, minimumWidth=80, width=100, stringConverter=self.formatDate),
			ColumnDefn(title='Time', valueGetter=2, minimumWidth=100, width=80),
			ColumnDefn(title='Precip', valueGetter=3, minimumWidth=50, width=50),
			ColumnDefn(title='Comment', valueGetter=4, minimumWidth=100, width=300),
			]
		self.weatherlist.SetColumns(cd)
		self.weatherlist.SetObjects(data)

	def formatDate(self, datestring):
		ds = str(datestring)
		ds = ds[4:6] + '/' + ds[6:8] + '/' + ds[0:4]
		return ds

	def HandleCellEditStarting(self, evt):
		if evt.subItemIndex == self.primarykeyindex:
			evt.Veto()
			wx.Bell()
			self.setMessage(messages[PRIMARY_KEY])

	def HandleCellEditFinished(self, evt):
		if evt.userCancelled:
			self.setMessage(messages[EDIT_CANCELLED])
			return
		update_statememt = "UPDATE %s SET %s=? WHERE %s = ?" % (self.tablename, self.weatherlist.columns[evt.subItemIndex].title, self.primarykey)
		self.db.updateData(update_statememt, (evt.rowModel[evt.subItemIndex], evt.rowModel[self.primarykeyindex]))

	# The lowly status bar message
	def setMessage(self, message=()):
		self.timedstatusbar.message=message[0]

if __name__ == '__main__':
	app = wx.App()
	MainWindow(None, title='Weather Recorder')
	app.MainLoop()
