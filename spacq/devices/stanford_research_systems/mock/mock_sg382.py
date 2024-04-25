from ...mock.mock_abstract_device import MockAbstractDevice
from ..sg382 import SG382

"""
Mock SG382 Signal Generator
*******This is not complete************
"""


class MockSG382(MockAbstractDevice, SG382):
	"""
	Mock interface for the SRS SG382
	"""

	def __init__(self, *args, **kwargs):
		self.mocking = SG382

		MockAbstractDevice.__init__(self, *args, **kwargs)

	def _reset(self):
		self.mock_state['frequency'] = 1000 # Hz
		self.mock_state['BNCAmplitude'] = 0.5 # V



name = 'SG382 Signal Generator'
implementation = MockSG382
