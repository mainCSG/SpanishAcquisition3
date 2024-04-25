from ...mock.mock_abstract_device import MockAbstractDevice
from ..dacsp927 import dacsp927

"""
Mock DAC SP 927 voltage source
*******This is not complete************
"""


class mockdacsp927(MockAbstractDevice, dacsp927):
	"""
	Mock interface for the DAC SP 927 voltage source
	"""

	def __init__(self, *args, **kwargs):
		self.mocking = dacsp927

		MockAbstractDevice.__init__(self, *args, **kwargs)

	def _reset(self):
		self.mock_state['frequency'] = 1000 # Hz
		self.mock_state['BNCAmplitude'] = 0.5 # V



name = 'dacsp927 Voltage Source'
implementation = mockdacsp927
