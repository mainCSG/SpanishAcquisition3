from ...mock.mock_abstract_device import MockAbstractDevice
from ..sim900 import sim900

"""
Mock Sim900+Sim928 voltage source
*******This is not complete************
"""


class Mock_sim900(MockAbstractDevice, sim900):
	"""
	Mock interface for the SRS SG382
	"""

	def __init__(self, *args, **kwargs):
		self.mocking = sim900

		MockAbstractDevice.__init__(self, *args, **kwargs)

	def _reset(self):
		self.mock_state['frequency'] = 1000 # Hz
		self.mock_state['BNCAmplitude'] = 0.5 # V



name = 'SIM900+SIM928 Voltage Source'
implementation = Mock_sim900
