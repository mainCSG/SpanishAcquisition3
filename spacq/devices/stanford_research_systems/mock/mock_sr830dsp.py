from ...mock.mock_abstract_device import MockAbstractDevice
from ..sr830dsp import SR830DSP

"""
Mock SR830 DSP Lockin Amplifier
"""


class MockSR830DSP(MockAbstractDevice, SR830DSP):
	"""
	Mock interface for the SRS SR830 DSP
	"""

	def __init__(self, *args, **kwargs):
		self.mocking = SR830DSP

		MockAbstractDevice.__init__(self, *args, **kwargs)

	def _reset(self):
		self.mock_state['reference_freq'] = 1000 # Hz
		self.mock_state['reference_amplitude'] = 0.5 # V



name = 'SR830 DSP'
implementation = MockSR830DSP
