###################### POWER SUPPLY CLASS #######################
### By Michael Parrott 8.14.2018
## Class that will take in a GPIB address, identify instrument (as one of 2, can be expanded)
## Will take desired operation and values, send correct string, verify state

import visa
import time

def returnValidDevices(rm):
	deviceList = rm.list_resources()
	validDevices = [None]*2
	for dev in deviceList:
		td = GPIBDevice(rm,dev)
		if td.type == -1:
			t = dev + " is not valid"
			print(t)
		elif td.type == 0:
			validDevices[0] = td
		else:
			validDevices[1] = td
	return validDevices

class GPIBDevice(object):

	def __init__(self,rm,visAdd):
		try:
			self.dev = rm.open_resource(visAdd)
			self.name = self.dev.query('*IDN?')
			#print(self.name)
			self.type = 0
			if 'HEWLETT' in self.name:
				self.type = 1
			elif 'LAMBDA' in self.name:
				self.type = 2
		except Exception as ex:
			self.dev = -1
			self.name = -1
			self.type = -1
			msg = "ERROR! This device does not exist!"
			#print msg

	def displayString(self,toPrint):
		self.dev.write('DISP ON')
		self.dev.write("DISP:TEXT " + "'" + toPrint + "'")

	def clearDisplay(self):
		self.dev.write('DISP:TEXT:CLE')

	def setCCVal(self,maxV,desI):
		desV = 'VOLT ' + str(maxV)
		desI = 'CURR ' + str(desI)
		self.dev.write(desV)
		time.sleep(.1)
		self.dev.write(desI)

	def setCVVal(self,desV,maxI):
		if self.type == 2:
			desV = ':VOLT ' + str(desV)
			self.dev.write(desV)
		else:
			desV = 'VOLT ' + str(desV)
			desI = 'CURR ' + str(maxI)
			self.dev.write(desI)
			time.sleep(.1)
			self.dev.write(desV)

	def setVRange(self,vRange):
		if vRange == 0:
			self.dev.write('VOLT:RANG P8V')
		else:
			self.dev.write('VOLT:RANGE P20V')

	def getCurrentVal(self):
		return self.dev.query("MEAS:CURR?")

	def getVoltageVal(self):
		return self.dev.query("MEAS:VOLT?")

	def outputOn(self):
		if self.type == 2:
			self.dev.write('OUTPUT:STATE 1')
		else:
			self.dev.write('OUTP ON')

	def outputOff(self):
		if self.type == 2:
			self.dev.write('OUTPUT:STATE 0')
		else:
			self.dev.write('OUTP OFF')

	def setStep(self,stepSize):
		self.dev.write('CURR:STEP:INCR ' + str(stepSize) )

	def stepUp(self):
		self.dev.write('CURR UP')

	def stepDown(self):
		self.dev.write('CURR DOWN')

	def write(self,val):
		self.dev.write(val)

	def query(self,val):
		return self.dev.query(val)

	def close(self):
		self.dev.close()