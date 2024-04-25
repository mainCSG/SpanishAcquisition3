import logging
log = logging.getLogger(__name__)

import numpy
import time

from spacq.interface.resources import Resource
from spacq.interface.units import Quantity
from spacq.tool.box import Synchronized

from ..abstract_device import AbstractDevice, AbstractSubdevice
from ..tools import quantity_unwrapped, quantity_wrapped, BinaryEncoder

"""
SRS Sim900+Sim928 module voltage sources
Control the output voltages on all the ports.
"""

class Port(AbstractSubdevice):
	"""
	An output port on the voltage source.
	"""
	def _setup(self):
		AbstractSubdevice._setup(self)

		# These values are used to tune the input values according to empirical error.
		self.gain = 1.0
		self.offset = 0.0

		# Resources.
		read_write = ['voltage']
		for name in read_write:
			self.resources[name] = Resource(self, name, name)

		self.resources['voltage'].units = 'V'

	@Synchronized()
	def _connected(self):
		AbstractSubdevice._connected(self)

		# Take an initial voltage reading (these get slow, so only use these to start, then just track what we've set)
		self.device.write('SNDT {0}, "VOLT?"'.format(self.num))
		outputMessage = self.device.ask_raw('GETN? {0}, 80'.format(self.num)) # This is a read command to port num

		# Parse the output message
		if outputMessage: #not empty
			try:
				byteCount = int(outputMessage[2:5])-2 # The last two bytes are the escape sequence
				if byteCount > 7: # There is a strange error will it will double read
					byteCount = (byteCount-2)/2
				result = float(outputMessage[5:(5+byteCount)])	
			except:
				result = -888
		else:
			result = -999
		self.currentVoltage = result
		

	def __init__(self, device, num, max_value, *args, **kwargs):
		"""
		Initialize the output port.
		device: The ch6VoltageSource to which this Port belongs.
		num: The index of this port.
		max_value: Largest value the port can produce.
		"""

		AbstractSubdevice.__init__(self, device, *args, **kwargs)

		self.num = num
		self.min_value = -max_value
		self.max_value = max_value
		self.currVoltage = -999
		
	@property
	@quantity_wrapped('V')
	def voltage(self):

		return self.currentVoltage
		
	@voltage.setter
	@quantity_unwrapped('V')
	def voltage(self, value):
		"""
		Set the voltage on this port, as a quantity in V.
		"""
		value = round(value, 3)
		resulting_voltage = value
		self.currentVoltage = value

		# Write out through Sim900, to port, and set voltage
#		self.device.write('SNDT {0}, "OPON"'.format(self.num))
		self.device.write('SNDT {0}, "VOLT {1}"'.format(self.num,resulting_voltage))
		
class sim900(AbstractDevice):
	"""
	Interface for the SRS Sim900+Sim928 voltage source
	"""
	
	def _setup(self):
		AbstractDevice._setup(self)

		self.ports = []
		for num in range(8):
			port = Port(self, num+1, 20, **self.port_settings) # Naming convention on sim900 goes 1 to 8
			self.ports.append(port)
			self.subdevices['port{0:02}'.format(num+1)] = port

	def __init__(self, port_settings=None, *args, **kwargs):
		"""
		Initialize the voltage source and all its ports.
		port_settings: A dictionary of values to give to each port upon creation.
		"""

		if port_settings is None:
			self.port_settings = {}
		else:
			self.port_settings = port_settings

		AbstractDevice.__init__(self, *args, **kwargs)

	@Synchronized()
	def _connected(self):
		AbstractDevice._connected(self)
		# Add any initialization here. Careful: if you reconnect it will run this
		self.write('*RST')


name = 'SIM900+SIM928 Voltage Source'
implementation = sim900
