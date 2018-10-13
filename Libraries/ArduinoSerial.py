#### Arduino Connection Class #####
import time,serial

class ArduinoSerial():

	def __init__(self,port,baudrate):
		self.device = serial.Serial(port,baudrate,timeout=0.5)
		time.sleep(6)
		# self.getRPM()
		# self.device.flushInput()

######  Function: getArduinoPacakge() #####
######  Requests data packet from arduino

	def getRPM(self):
		## Request and receive package
		# if self.device.inWaiting():
		# 	self.device.readline()
		self.device.flushInput()
		toWrite = '1'
		self.device.write(toWrite.encode())
		
		while self.device.in_waiting == 0:
			time.sleep(0.02)
		data = self.device.readline().decode()
		data = data.rstrip('\r\n')

		#data = float(data)
		# data = data.lstrip('b')
		# data = data.rstrip('\r\n')
		# counter = 0
		# while len(data) == 0:
		# 	toWrite = '1'
		# 	self.device.write(toWrite.encode())
		# 	time.sleep(0.1)
		# 	data = self.device.readline()
		# 	counter += 1
		# 	if counter == 5:
		# 		## If can't get package, return -1
		# 		return -1
		# ## When data length is > 0, return
		return data


	def sendEShutOff(self):
		self.device.flushInput()
		toWrite = "2"
		self.device.write(toWrite.encode())
		#time.sleep(0.1)
		while self.device.in_waiting == 0:
			time.sleep(0.01)
		response = self.device.readline().decode()
		response = data.rstrip('\r\n')