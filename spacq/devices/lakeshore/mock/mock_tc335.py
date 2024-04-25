import random

from ...mock.mock_abstract_device import MockAbstractDevice
from ..tc335 import TC335

"""
Mock Lakeshore 335 Temperature Controller
"""

class MockTC335(MockAbstractDevice, TC335):
	"""
	Mock interface for Lakeshore 335 Temperature Controller.
	"""

	def __init__(self, *args, **kwargs):
		self.mocking = TC335

		MockAbstractDevice.__init__(self, *args, **kwargs)
		
		self.mock_state = {}
		self.mock_state['readingstatus'] = 0
		self.mock_state['read_only'] = ['temperature', 'powerA']#, 'powerB'] # added power A and B
		self.mock_state['read_write'] = ['setTempA', 'rangeA'] #'setTempB' 'rangeB'] # addded this line
		
	def _reset(self):
		pass
		
	def write(self, message, result=None, done=False):
		if not done:
			cmd, args, query = self._split_message(message)
					
			if cmd[0] == 'rdgst' and query:
				result = self.mock_state['readingstatus']
				done = True
			elif cmd[0] == 'krdg' and query:
				result = random.randint(5,100)
				done = True

		MockAbstractDevice.write(self, message, result, done)


name = '335 Temperature Controller'
implementation = MockTC335
