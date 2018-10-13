#!#!#!#!#!#!#!#!#!#!#!#!#!#!# DynoGui !#!#!#!#!#!#!#!#!#!#!#!#!#!#!#!#!#
'''
By Michael Parrott, started on 9/18/18
GUI for LV Dyno Operation, provides live view of current test parameters, inputs for test voltages/temps,
logging file
                                              ____
  ___                                      .-~. /_"-._
`-._~-.                                  / /_ "~o\  :Y
      \  \                                / : \~x.  ` ')
      ]  Y                              /  |  Y< ~-.__j
     /   !                        _.--~T : l  l<  /.-~
    /   /                 ____.--~ .   ` l /~\ \<|Y
   /   /             .-~~"        /| .    ',-~\ \L|
  /   /             /     .^   \ Y~Y \.^>/l_   "--'
 /   Y           .-"(  .  l__  j_j l_/ /~_.-~    .
Y    l          /    \  )    ~~~." / `/"~ / \.__/l_
|     \     _.-"      ~-{__     l  :  l._Z~-.___.--~
|      ~---~           /   ~~"---\_  ' __[>
l  .                _.^   ___     _>-y~
 \  \     .      .-~   .-~   ~>--"  /
  \  ~---"            /     ./  _.-'
   "-.,_____.,_  _.--~\     _.-~
               ~~     (   _}       -Row
                      `. ~(
                        )  \
                  /,`--'~\--'~\
                  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
'''
import visa
import nidaqmx
import csv
import math
from collections import deque
#from Libraries.ArduinoSerial import *
from Libraries.GPIBDevice import *
from pytl.base.utils import setup_logger
from Libraries.chamber_F4T import *
from pytl.equipment.ni.nidaq import NIDaq
from pytl.base.utils import email
import atexit


import sys,time,os
from PyQt5.QtWidgets import *# QApplication, QWidget,QPushButton, QMainWindow,QCheckBox, QRadioButton, QLineEdit, QFormLayout
from PyQt5.QtGui import *
from PyQt5.QtCore import *

class MainWindowTest(QWidget):
	class Test(object):
		def __init__(self,voltage,temp):
			self.volt = voltage
			self.temp = temp

	changeTrigger = pyqtSignal()

	def __init__(self):
		super().__init__()
		self.initUI()
		#initialize state variables
		#self.changeTrigger = pyqtSignal()
		self.changeTrigger.connect(self.value_changed)
		self.testVoltages = ''
		self.testTemps = ''
		self.fileName = ''
		self.stopPressed = False
		self.connected = False
		self.MAX_CURRENT_VAL = 15
		self.motorStepSize = 0.008
		self.DUT_POWER = None
		self.Scrubber_Power = None
		self.STABLE_DELAY = 4
		self.COOLING_DELAY = 15
		self.chamber = None
		self.THERMAL_MAX_DELAY = 3000
		self.THERMAL_POST_DELAY = 600
		#self.changeTrigger.emit()

	def initUI(self):
		#self.statusBar().showMessage('Ready')
		self.setGeometry(200,200,600,370)
		self.setWindowTitle('Dyno GUI')

		self.makeInputSide()

		#self.check1 = QRadioButton()
		self.makeOutputSide()
		# startbtn = QPushButton('Start',self)
		# stopbtn = QPushButton('Stop',self)
		# nextbtn = QPushButton('next',self)
		# vbox = QVBoxLayout()
		# vbox.addWidget(startbtn)
		# vbox.addWidget(stopbtn)
		overLay = QHBoxLayout()
		overLay.addLayout(self.leftSideLayout)
		overLay.addStretch()
		overLay.addLayout(self.rightSideLayout)
		overLay.addStretch()
		#overLay.addStretch(1)
		self.setLayout(overLay)


		# leftLayout = QVBoxLayout()
		# layout.addWidget(self.)

		self.show()

	def makeInputSide(self): 
		## Start/Stop Button
		self.leftSideLayout = QVBoxLayout()

		self.startbtn = QPushButton('Start',self)
		self.startbtn.clicked.connect(self.respondToStart)#QApplication.instance().quit)
		self.startbtn.resize(self.startbtn.sizeHint())
		startImg = QPixmap('startButton.jpg')
		startIcon = QIcon('startButton.jpg')
		self.startbtn.setIcon(startIcon)
		# lbl = QLabel()
		# lbl.setPixmap(startImg)
		# self.startbtn.setIcon(QIcon('/Images/startIcon.jpeg'))
		# self.startbtn.setIconSize(QSize(100,100))
		#self.startbtn.move(60,50)
		self.stopbtn = QPushButton('Stop',self)
		self.stopbtn.clicked.connect(self.respondToStop)#QApplication.instance().quit)
		self.stopbtn.resize(self.stopbtn.sizeHint())
		self.stopbtn.setVisible(False)

		self.connectbtn = QPushButton('Connect to devices',self)
		self.connectbtn.clicked.connect(self.connectDevices)
		self.connectbtn.resize(self.connectbtn.sizeHint())

		self.connectLbl = QLabel('Not Connected')

		inputForm = QFormLayout()

		# Input TextField
		vInL = QLabel('Desired Voltages')
		self.vIn = QLineEdit(self)
		#self.vIn.move(30,100)
		#self.vIn.returnPressed.connect(self.parseVoltages)

		tLabel = QLabel('Test Temps')
		self.tInBox = QLineEdit(self)

		self.fileNameBox = QLineEdit(self)
		fileNameLabel = QLabel('Logfile Name')

		stallCurrentLabel = QLabel('Max. Scrubber Current')
		self.stallCurrent = QLineEdit(self)	
		self.stallCurrent.setValidator(QDoubleValidator())
		self.stallCurrent.returnPressed.connect(self.getScrubberCurrentInput)
		#self.fileNameBox.move(30,150)
		#self.fileNameBox.returnPressed.connect(self.parseName)

		connectLay = QHBoxLayout()
		connectLay.addWidget(self.connectbtn)
		connectLay.addWidget(self.connectLbl)
		self.leftSideLayout.addLayout(connectLay)
		self.leftSideLayout.addStretch()
		#self.leftSideLayout.addStretch()
		self.leftSideLayout.addWidget(self.startbtn)
		self.leftSideLayout.addWidget(self.stopbtn)
		#self.leftSideLayout.addWidget(lbl)
		self.leftSideLayout.addStretch()
		inputForm.addRow(vInL,self.vIn)
		inputForm.addRow(tLabel,self.tInBox)
		inputForm.addRow(fileNameLabel,self.fileNameBox)
		inputForm.addRow(stallCurrentLabel,self.stallCurrent)

		#self.leftSideLayout.addWidget(self.vIn)
		self.leftSideLayout.addLayout(inputForm)
		self.leftSideLayout.addStretch()

		self.timerDisplay = QLCDNumber()
		self.leftSideLayout.addWidget(self.timerDisplay)

	def makeOutputSide(self):
		self.rightSideLayout = QGridLayout()
		vLabel = QLabel('Voltage')
		self.vVal = QLCDNumber()
		iLabel = QLabel('Current')
		self.iVal = QLCDNumber()
		pLabel = QLabel('Power')
		self.pVal = QLCDNumber()
		wLabel = QLabel('RPM')
		self.wVal = QLCDNumber()
		tLabel = QLabel('Torque')
		self.tVal = QLCDNumber()
		eLabel = QLabel('Efficiency')
		self.eVal = QLCDNumber()
		dFont = QFont("Times",16,QFont.Bold)

		tempLabel = QLabel('TC Temp')
		self.tempVal = QLCDNumber()

		scrubLabel = QLabel('Scrubber Current')
		self.scrubVal = QLCDNumber()

		self.vVal.resize(self.vVal.sizeHint())
		self.iVal.resize(self.iVal.sizeHint())
		self.pVal.resize(self.pVal.sizeHint())
		self.wVal.resize(self.wVal.sizeHint())
		self.tVal.resize(self.tVal.sizeHint())
		self.eVal.resize(self.eVal.sizeHint())

		pal = self.iVal.palette()
		pal.setColor(pal.WindowText,QColor(255,0,0))
		self.vVal.setPalette(pal)
		self.iVal.setPalette(pal)
		self.pVal.setPalette(pal)
		self.wVal.setPalette(pal)
		self.tVal.setPalette(pal)
		self.eVal.setPalette(pal)
		self.tempVal.setPalette(pal)
		self.scrubVal.setPalette(pal)


		self.vVal.setFont(dFont)
		self.iVal.setFont(dFont)
		self.pVal.setFont(dFont)
		self.wVal.setFont(dFont)
		self.tVal.setFont(dFont)
		self.eVal.setFont(dFont)
		self.tempVal.setFont(dFont)
		self.scrubVal.setFont(dFont)

		self.rightSideLayout.addWidget(vLabel,0,0)
		self.rightSideLayout.addWidget(self.vVal,0,1)
		self.rightSideLayout.addWidget(iLabel,0,2)
		self.rightSideLayout.addWidget(self.iVal,0,3)
		self.rightSideLayout.addWidget(wLabel,1,2)
		self.rightSideLayout.addWidget(self.wVal,1,3)
		self.rightSideLayout.addWidget(tLabel,1,0)
		self.rightSideLayout.addWidget(self.tVal,1,1)
		self.rightSideLayout.addWidget(pLabel,2,0)
		self.rightSideLayout.addWidget(self.pVal,2,1)
		self.rightSideLayout.addWidget(eLabel,2,2)
		self.rightSideLayout.addWidget(self.eVal,2,3)

		self.rightSideLayout.addWidget(tempLabel,3,0)
		self.rightSideLayout.addWidget(self.tempVal,3,1)
		self.rightSideLayout.addWidget(scrubLabel,3,2)
		self.rightSideLayout.addWidget(self.scrubVal,3,3)


		self.rightSideLayout.setVerticalSpacing(30)
		print('Output NOW!!!!')

	def respondToStart(self):
		self.stopPressed = False
		testVoltages = None
		curFileName = None
		scrubberMaxCurrent = None
		if self.connected:
			self.startbtn.setVisible(False)
			self.stopbtn.setVisible(True)
		else:
			print('Cant Start! Devices not connected')
			return
		testVoltages = self.getTestVoltages()
		logFile = self.getFileName()
		FINAL_CURRENT = self.getScrubberCurrentInput()
		testList = list()
		testTemps = self.getTestTemps()
		starTime = time.time()
		self.vVal.display(9)

		# self.DUT_POWER.setCVVal(10,10)
		# self.DUT_POWER.outputOn()
		# while time.time() - starTime < 10:
		# 	data = self.getData()
		# 	self.displayData(data,9)
		# self.DUT_POWER.outputOff()



		for temp in testTemps:
			for volt in testVoltages:
				tempTest = self.Test(volt,temp)
				testList.append(tempTest)
		lastTemp = -100
		x = 0
		for test in testList:
			print('Currently in test: ' + str(test.volt) + 'V')
			############ Thermal Chamber Setting ###########
			if test.temp != lastTemp:
				self.setThermalState(test.temp)
				lastTemp = test.temp

			preTime = time.time()

			while (not self.ThermalsEqualized(test.temp)):
				print("Thermals are not stable yet")
				if time.time() - preTime > self.THERMAL_MAX_DELAY:
					print('I couldnt do it :(')
					break
				self.liveDelay(5)
				data = self.getData()
				self.displayData(data,test.volt)
				QApplication.processEvents()
				if self.stopPressed == True:
					return

			print('Thermals Equalized, delaying 10 minutes')
			# if x = 0:
			# 	self.liveDelay(1)
			# 	x = x + 1
			# else:
			# 	self.liveDelay(self.THERMAL_POST_DELAY)
			self.liveDelay(self.THERMAL_POST_DELAY)
			print('Delay over, beginning test')
			print('Test temp is: ' + str(test.temp))
			print('Test volt is: ' + str(test.volt))
			########### Thermal Chamber Complete ###########
			curTest = dict()
			logPath = logFile + "_" + str(test.temp) + "C_" + str(test.volt) + "V.csv"
			myFile = open(logPath,'w')
			self.mycsv = csv.writer(myFile,delimiter=',',lineterminator='\r')
			#columnTitleRow = "Index,Torque,Current,RPM\n"
			self.mycsv.writerow(['Index','Torque','Current','RPM','Power Out','Power In','Efficiency'])
			self.DUT_POWER.setCVVal(test.volt,self.MAX_CURRENT_VAL)

			# First, identify stall point 
				# Should I jsut send known 
			#self.getStallPoint(test.volt)

			self.runFullTest(test.volt, FINAL_CURRENT)

			myFile.close()

	def runFullTest(self,voltage, FINAL_CURRENT):
		#print('Running test at:' + str(voltage))

		stallCurrent = self.getStallPoint(voltage)
		if stallCurrent > FINAL_CURRENT:
			stallCurrent = FINAL_CURRENT
		motorSteps = self.getTorqueDist(stallCurrent)
		print('Beginning full run')
		self.DUT_POWER.outputOn()
		self.vVal.display(voltage)
		QApplication.processEvents()
		ptime = time.time()
		while time.time() - ptime < self.STABLE_DELAY:
			data = self.getData()
			self.displayData(data,voltage,0)

		# time.sleep(4)
		data = self.getData()
		self.recordAllValues(0,data,voltage)
		self.DUT_POWER.outputOff()
		self.Scrubber_Power.setCCVal(16,0)
		#currentVal = self.motorStepSize
		#sleep
		# self.Scrubber_Power.outputOn()
		#sleep
		self.liveDelay(5)
		
		startTime = time.time()
		i = 1
		# self.Scrubber_Power.setCCVal(16,motorSteps[i])
		while i < 8:
			curTime = time.time()
			self.DUT_POWER.outputOn()
			self.Scrubber_Power.setCCVal(16,motorSteps[i])
			self.Scrubber_Power.outputOn()

			# Wait for stability, update screen in the meantime
			print('I is ' + str(i))
			while time.time() - curTime < self.STABLE_DELAY:
				# update display
				if self.stopPressed:
					break
				data = self.getData()
				self.displayData(data,voltage,motorSteps[i])
			curTime = time.time()
			# Record Data Point
			data = self.getData()
			self.recordAllValues(i,data,voltage)

			self.Scrubber_Power.outputOff()
			self.liveDelay(.1)
			self.DUT_POWER.outputOff()

			i = i + 1

			while time.time() - curTime < self.COOLING_DELAY:
				data = self.getData()
				self.displayData(data,voltage,0)
				QApplication.processEvents()
				if self.stopPressed:
					break
		self.Scrubber_Power.outputOff()
		self.DUT_POWER.outputOff()
		print('Finished test!')
		# need to reset start button
		self.stopbtn.hide()
		self.startbtn.show()

	def getStallPoint(self,voltage):
		print('Trying to find stall now')
		self.DUT_POWER.outputOn()  		# initiate motor 
		self.Scrubber_Power.setCCVal(16,0)
		self.Scrubber_Power.outputOn()

		tempCur = 0.05
		curStep = .005
		data = self.getData()
		while data['Frequency'] != 0:
			tempCur = tempCur + curStep
			if tempCur > 0.13:
				break
			self.Scrubber_Power.setCCVal(16,tempCur)
			self.liveDelay(.2)
			data = self.getData()

		self.recordAllValues(-1,data,voltage)
		self.liveDelay(0.3)
		
		self.Scrubber_Power.setCCVal(16,0)
		self.Scrubber_Power.outputOff()
		self.DUT_POWER.outputOff()
		print('Stall current acquired, Ts = ' + str(tempCur))
		return tempCur-curStep

	def displayData(self,data,voltage,scrubCurrent=0):
		# need to update on screen values
		i = data['Current']
		w = data['Frequency']
		t = abs(data['Voltage_0']/5)
		p = t*w*2*math.pi#must convert
		if i == 0:
			i = 0.01
		e = p/(i*voltage)*100

		temp = data['Temp']
		if 'Temp' not in data.keys():
			data['Temp'] = -100

		self.iVal.display(i)
		self.wVal.display(w*60)
		self.tVal.display(t)
		self.pVal.display(p)
		self.eVal.display(e)
		self.scrubVal.display(scrubCurrent)
		self.tempVal.display(temp)
		QApplication.processEvents()

	def getTorqueDist(self,maxVal):
		desired = [.25,.2,.15,.125,.1,.075,.05,.05]
		actual = list()
		final = list()
		lastVal = 0
		for i in desired:
			curVal = (lastVal + i)
			actual.append(curVal)
			lastVal = curVal
		for i in actual:
			final.append(i*maxVal)
		return final

	def getData(self):
		try:
			data = self.daq.get_data(timeout=0.4)
			#data['RPM'] = getEncoderSpeed()
			data['Current'] = float(self.DUT_POWER.getCurrentVal())
			data['Temp'] = float(self.chamber.get_temperature())
			return data
		except nidaqmx.errors.DaqError:
			data = dict()
			data['Voltage_0'] = 0
			data['Frequency'] = 0
			data['Current'] = float(self.DUT_POWER.getCurrentVal())
			return data
		except Exception as ex:
			msg = str(ex)
			#sendErrorReport('getData',msg)
			#sys.exit()

	def recordAllValues(self,index,data,voltage):
		#will have csv.write(structured log line)
		# print('This is recording')
		torque = abs(data['Voltage_0']/5)

		# print('Got torque')
		current = data['Current']
		rpm = data['Frequency']*60
		powerOut = torque*data['Frequency']*2*math.pi#must convert
		powerIn = current*voltage
		eff = powerOut/powerIn
		row = [index,torque,current,rpm,powerOut,powerIn,eff]
		#curTest(i) = row
		self.mycsv.writerow(row)
		return data

	def connectDevices(self):
		print('Attempting to connect')
		self.rm = visa.ResourceManager()
		# DAQ Initialization
		try:
			self.daq = NIDaq('newConfig3.ini') 
		except nidaqmx.errors.DaqError as er:
			print('Failed to connect to daq!')
			self.connected = False
		try:
			scopes = returnValidDevices(self.rm)
			self.DUT_POWER = scopes[1]
			self.Scrubber_Power = scopes[0]
			self.connected = True
			atexit.register(self.exitStop,dut_power = self.DUT_POWER, scrubber_power = self.Scrubber_Power)#, DUT_Power = self.DUT_POWER,Scrubber_Power = self.Scrubber_Power)
		except Exception as ex:
			print(str(ex))
			self.connected = False

		try:
			main_logger = setup_logger(logging.getLogger(),level=logging.INFO)
			main_logger.info('Connecting to chamber')
			ip_addr = '192.168.0.222'
			self.chamber = F4T(host=ip_addr)
			print('Connected to chamber!')
		except Exceptions as ex:
			print(str(ex))
			self.connected = False
		if self.daq != None and self.DUT_POWER != None:
			self.connectLbl.setText('Connected!')
			self.connectbtn.hide()
		else:
			print('Didnt connect!')

	def ThermalsEqualized(self,desiredTemp):
		try:
			temp = self.chamber.get_temperature() - desiredTemp

			if abs(temp) > 1:
				print('Not equal, current temp is ' + str(temp))
				return False
			else:
				return True
		except Exception as ex:
			print('Could not connect!')

	def setThermalState(self,desiredTemp):
		print('Setting thermal state to:' + str(desiredTemp) + ' C')
		try:
			self.chamber.setTemperature(desiredTemp)
		except Exception as ex:
			print('Couldnt set thermal temp')

	def getTestVoltages(self):
		text = self.vIn.text()
		voltages = list()
		if text == '':
			voltages = [9]
		else:
			voltages = [float(x) for x in text.split(',')]
		return voltages

	def getTestTemps(self):
		text = self.tInBox.text()
		testTemps = list()
		if text == '':
			testTemps = [-40,20,80]
		else:
			testTemps = [int(x) for x in text.split(',')]
		return testTemps

	def getFileName(self):
		text = self.fileNameBox.text()
		if text == '':
			fname = 'sample'
		else:
			fname = text
		return fname

	def getScrubberCurrentInput(self):
		text = self.stallCurrent.text()
		if text == '':
			text = 0.08
		else:
			text = float(text)
		return text

	def respondToStop(self):
		self.startbtn.setVisible(True)
		self.stopbtn.setVisible(False)
		self.stopPressed = True
		print('Stopping')

	def parseVoltages(self):
		text = self.vIn.text()
		print('Got the line! Its ' + text)

	def parseName(self):
		text = self.fileNameBox.text()
		print('File name is ' + text)

	@pyqtSlot()
	def value_changed(self):
		oldText = float(self.vVal.text())
		newVal = oldText + 1
		self.vVal.setText(str(newVal))
		print('Trying to change value')
		#self.vVal.setText(str(value))


	def eStopAtExit(self):
		print('Trying estop now')
		if self.DUT_POWER != None:
			self.Scrubber_Power.outputOff()
			self.DUT_POWER.outputOff()
			self.DUT_POWER = None
			self.Scrubber_Power = None

	def exitStop(self,dut_power,scrubber_power):
		print('atexit stop now')
		if dut_power != None:
			scrubber_power.outputOff()
			dut_power.outputOff()
			dut_power = None
			scrubber_power = None

	def closeEvent(self,event):
		print('close event')
		self.eStopAtExit()
		event.accept()

	def liveDelay(self,delayTime):
		print('this is liveDelay')
		preTime = time.time()
		tLeft = time.time() - preTime
		while tLeft < delayTime:
			QApplication.processEvents()
			tLeft = time.time() - preTime
			self.timerDisplay.display(delayTime - tLeft)
		self.timerDisplay.display(0)

######################################### Dyno Test Operation Section #############################



if __name__ == '__main__':
	app = QApplication(sys.argv)
	w = MainWindowTest()
	# time.sleep(5)
	# print('sending now')
	# mySig = pyqtSignal(int)
	# mySig.connect(w.value_changed)
	# mySig.emit(5)
	# w.setWindowTitle('Hello World!')
	# w.show()
	sys.exit(app.exec_())