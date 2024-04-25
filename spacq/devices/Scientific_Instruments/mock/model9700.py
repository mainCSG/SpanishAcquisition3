import random

from ...mock.mock_abstract_device import MockAbstractDevice
from ..model9700 import Model9700

"""
Mock Scientific Instruments 9700 Temperature Controller
"""

class MockModel9700(MockAbstractDevice):
	"""
	Mock interface for Scientific Instruments Model 9700 Temperature Controller.
	"""

	def __init__(self, *args, **kwargs):
		self.mocking = Model9700

		MockAbstractDevice.__init__(self, *args, **kwargs)
		
		self.mock_state = {}

name = 'Model 9700 Temperature Controller'
implementation = MockModel9700
