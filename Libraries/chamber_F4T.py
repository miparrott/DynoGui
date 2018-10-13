import socket
import time
import logging
import sys
from pytl.base.utils import setup_logger
# Need to configure your TCP settings to communicate!!
# Check the F4T section here: https://confluence.teslamotors.com/display/REL/Instrument+Communications+and+Connection+Troubleshooting


class Client(object):
    host = None
    port = None
    size = None

    def __init__(self, host, port, size = 1024):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.host = host
        self.port = port
        self.size = size

    def send_message(self, message: str, response=True):

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.host, self.port))
        except socket.error as e:
            if s:
                s.close()
            self._logger.info( "Could not open socket: {}".format(str(e)))
            return None
        message = message.encode()
        s.send(message)

        if response is True:
            msg_received = s.recv(self.size)
        else:
            msg_received = None
        msg_received = msg_received.decode('utf-8')
        s.close()
        return msg_received

    def send_multi_message(self, message, times):
        message = message.encode()
        for i in range(times):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((self.host, self.port))
            except socket.error as e:
                if s:
                    s.close()
                self._logger.info("Could not open socket: {}".format(str(e)))
                sys.exit(1)
            s.send(message)
            response = s.recv(self.size)
            response = response.decode('utf-8')
            s.close()
            if response != '':
                break
        return response



class F4T(Client):
    """
    To use this class with a static IP, need to configure
    your computer's LAN settings: http://www.testequity.com/static/470/

    Notes:
    1) This chamber does not always receive messages using the Client class' send_message function,
    resulting in output of ''. Instead, this class uses the send_multi_message function to send messages until a response is received
    Number of tries is controlled by self.__message_timeout

    2) Regardless of F4T controller temperature unit settings, ethernet communication with chamber is in Fahrenheit.
    All inputs/outputs to this class are Celsius, with conversion happening internally to this class using self.f_to_c() and self.c_to_f().
    """

    black_listed = ['black_listed','data','host','port','size','message_timeout','humidity_flag']
    host = None
    port = None
    size = None
    temperature = None
    humidity = None
    SP_temperature = None
    SP_humidity = None
    message_timeout = None
    humidity_flag = True

    def __init__(self, host, port = 5025, size = 1024):
        # Initialize base chamber variables, stop chamber operation
        self.host = host
        self.port = port
        self.size = size
        self._logger = logging.getLogger(self.__class__.__name__)
        self.message_timeout = 3 # Number of times chamber is pinged before giving up
        super(F4T,self).__init__(self.host,self.port,self.size)


    def get_data(self):
        self.get_temperature()
        self.get_humidity()
        self.get_setpoint_temperature()
        self.get_setpoint_humidity()
        self.data = dict([(k,v) for k,v in self.__dict__.items() if k not in self.black_listed])

    def get_temperature(self):
        message = ':SOURCE:CLOOP1:PVALUE?\n'
        response = self.send_multi_message(message, self.message_timeout)
        try:
            self.temperature = self.f_to_c(response)
        except:
            self._logger.info("Chamber did not respond after %d tries.")

        return self.temperature

    def get_humidity(self):
        message = ':SOURCE:CLOOP2:PVALUE?\n'
        response = self.send_multi_message(message, self.message_timeout)
        try:
            self.humidity = float(response)
        except:
            self._logger.info("Chamber did not respond after %d tries.")

        return self.humidity

    def get_setpoint_temperature(self):
        message = ':SOURCE:CLOOP1:SPOINT?\n'
        response = self.send_multi_message(message, self.message_timeout)
        try:
            self.SP_temperature = self.f_to_c(response)
        except:
            self._logger.info( "Chamber did not respond after %d tries.")

        return self.SP_temperature

    def get_setpoint_humidity(self):
        message = ':SOURCE:CLOOP2:SPOINT?\n'
        response = self.send_multi_message(message, self.message_timeout)
        try:
            self.SP_humidity = float(response)
        except:
            self._logger.info("Chamber did not respond after %d tries.")

        return self.SP_humidity

    def setTemperature(self, SP_temp):
        self.SP_temperature = str(SP_temp)
        message = ':SOURCE:CLOOP1:SPOINT {} \n'.format(self.c_to_f(self.SP_temperature))
        self.send_multi_message(message,self.message_timeout)

    def set_humidity(self, SP_hum):
        self.SP_humidity = str(SP_hum)
        message = ':SOURCE:CLOOP2:SPOINT {} \n'.format(self.SP_humidity)
        self.send_multi_message(message,self.message_timeout)

    def f_to_c(self,temp):
        temp = (float(temp) - 32)*(5.0/9.0)
        return temp

    def c_to_f(self,temp):
        temp = (float(temp)*1.8) + 32
        return temp

if __name__ == "__main__":
    import time
    from pytl.base.utils import setup_logger

    main_logger = setup_logger(logging.getLogger(),level=logging.INFO)
    main_logger.info('Connecting to chamber')
    ip_addr = '192.168.0.222'
    chamber = F4T(host=ip_addr)

    chamber.setTemperature(40)
    main_logger.info('Setting temp')
    while True:
        main_logger.info(chamber.get_temperature())
        time.sleep(1)