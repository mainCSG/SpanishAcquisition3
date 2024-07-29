"""
	Device driver for the Qblox SPI Rack with 2 D5a modules installed.

	Note:
		This driver likely contains some redundant code that is a carry over
		from other working Spanish Acquisition device drivers. Since the implementation interface
		is not clear, this extra code has been left in to ensure the device still works properly.

		The mock device and tests for this device are untested.

	Authors: Luke Dyer, Noah Stieler
"""

import logging
log = logging.getLogger(__name__)

from qblox_instruments import SpiRack

from spacq.interface.resources import Resource
from spacq.tool.box import Synchronized

from ..abstract_device import AbstractDevice, AbstractSubdevice
from ..tools import quantity_wrapped, quantity_unwrapped

#These addresses are written on the side of each D5a module.
#You need to physically remove the module from the SPI rack to get the address.
D5A_ADDRESS_1 = 8 #First D5a module from the left
D5A_ADDRESS_2 = 7 #Second D5a moduel from the left

class D5aDAC(AbstractSubdevice):
	"""
	Represents a digital to analog converter (DAC) belonging to a D5a module.
	"""
	def _setup(self):
		AbstractSubdevice._setup(self)

		# We don't use these variable but they maybe used somewhere else
		# as Python doesn't have private member variables.
		self.gain = 1.0
		self.offset = 0.0

		# Resources.
		self.resources['voltage'] = Resource(self, 'voltage', 'voltage')
		self.resources['voltage'].units = 'V'

	@Synchronized()
	def _connected(self):
		AbstractSubdevice._connected(self)
		
	def __init__(self, device, dac, *args, **kwargs):
		"""
		Initialize the output port.
		device: The QBlox SPI rack to which this Module belongs.
		dac: SPI Rack DAC from one of the D5A modules
		"""

		self.dac = dac

		AbstractSubdevice.__init__(self, device, *args, **kwargs)

		self.currentVoltage = 0
		
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
		self.currentVoltage = value

		self.dac.voltage(value)
		
class SPIRack(AbstractDevice):
	"""
	Interface for the QBLOX SPI rack
	"""
	
	def _setup(self):
		AbstractDevice._setup(self)

		return

	def __init__(self, port_settings=None, *args, **kwargs):
		"""
		Initialize the voltage source and all its ports.
		port_settings: A dictionary of values to give to each port upon creation.
		"""

		if port_settings is None:
			self.port_settings = {}
		else:
			self.port_settings = port_settings

		kwargs["autoconnect"] = False

		AbstractDevice.__init__(self, *args, **kwargs)

	@Synchronized()
	def _connected(self):
		AbstractDevice._connected(self)
	
	def connect(self):

		NUMBER_OF_DACS = 16

		self.device = SpiRack("SpiRack", self.connection_resource["resource_name"])
			
		self.device.add_spi_module(D5A_ADDRESS_1, "D5a", "module1")
		self.device.add_spi_module(D5A_ADDRESS_2, "D5a", "module2")

		for D5aNum in range(1,3):
			for i in range(NUMBER_OF_DACS):
				# i+1 so GUI labelling of DACS matches physical label on the device
				exec("self.subdevices['D5a_' + str(D5aNum) + '_DAC_' + str(i+1)] = D5aDAC(self, self.device.module{}.dac{})".format(D5aNum, i))
		return

name = 'QBlox SPI Rack'
implementation = SPIRack