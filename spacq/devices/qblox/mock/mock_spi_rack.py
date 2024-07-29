import random

from ...mock.mock_abstract_device import MockAbstractDevice
from ..spi_rack import SPIRack

"""
Mock SPI RACk
"""


class MockSPIRack(MockAbstractDevice, SPIRack):
	"""
	Mock interface for the Sample ABC1234.
	"""

	def __init__(self, *args, **kwargs):
		self.mocking = SPIRack

		MockAbstractDevice.__init__(self, *args, **kwargs)

	def _reset(self):
		self.mock_state['setting'] = 'default value'



name = 'QBlox SPI Rack'
implementation = MockSPIRack
