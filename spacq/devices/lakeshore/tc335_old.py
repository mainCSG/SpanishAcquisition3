import logging
log = logging.getLogger(__name__)

from spacq.interface.resources import Resource
from spacq.tool.box import Synchronized

from ..abstract_device import AbstractDevice
from ..tools import quantity_wrapped

"""
Lakeshore 335 Temperature Controller

Read temperature (TODO: Add more functionality)
"""

class TC335(AbstractDevice):
	"""
	Interface for Lakeshore 335 Temperature Controller
	"""
	
	def _setup(self):
		AbstractDevice._setup(self)

		# Resources.
		self.read_only = ['temperature']
		for name in self.read_only:
			self.resources[name] = Resource(self, name)

		self.resources['temperature'].units = 'K'
								
	@Synchronized()
	def _connected(self):
		AbstractDevice._connected(self)

		# TODO: Allow for measurements other than DC voltage.
		# self.write('configure:voltage:dc')

	@Synchronized()
	def reset(self):
		"""
		Reset the device to its default state.
		"""

		log.info('Resetting "{0}".'.format(self.name))
		self.write('*rst')


	@property
	@quantity_wrapped('K')
	@Synchronized()
	def temperature(self):
		"""
		The value measured by the device, as a quantity in V.
		"""

		self.status.append('Taking reading')

		try:
			log.debug('Getting reading.')
			status = int(self.ask('rdgst?'))
			if status == 0:
				result = float(self.ask('krdg?'))
			elif status <= 17:
				result = -1 #This corresponds to T.UNDER
			else:
				result = -2 # This should correspond to S.OVER, or other errors

			log.debug('Got reading: {0}'.format(result))

			return result
		finally:
			self.status.pop()


name = '335 Temperature Controller'
implementation = TC335
