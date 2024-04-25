import logging
log = logging.getLogger(__name__)

from spacq.interface.resources import Resource
from spacq.tool.box import Synchronized

from ..abstract_device import AbstractDevice
from ..tools import quantity_wrapped

"""
Scientific Instruments 9700 Temperature Controller
"""

class Model9700(AbstractDevice):
	"""
	Interface for Scientific Instruments 9700 Temperature Controller
	"""
	
	def _setup(self):
		AbstractDevice._setup(self)

		# Resources.
		self.read_only = ['temperature', 'power']
		for name in self.read_only:
			self.resources[name] = Resource(self, name)

		self.resources['temperature'].units = 'K'
								
	@Synchronized()
	def _connected(self):
		AbstractDevice._connected(self)

	@property
	@quantity_wrapped('K')
	@Synchronized()
	def temperature(self):
		"""
		The value measured by the device, as a quantity in K.
		"""

		while True:
			# Sometimes does not answer the correct query, so need to ask until we get the desired response
			result = self.device.query('TA?')
			if 'TA' in result:
				return float(result[2:])
			else:
				continue

	@property
	def power(self):
		'''
		The value of the PID as a percentage.
		'''

		# Sometimes does not answer the correct query, so need to ask until we get the desired response
		while True:
			result = self.device.query('HTR?')
			if 'HTR' in result:
				return float(result[3:])
			else:
				continue

name = 'Model 9700 Temperature Controller'
implementation = Model9700
