import random

from ...mock.mock_abstract_device import MockAbstractDevice
from ..nwa8753et import NWA8753ET

"""
Mock
"""


class MockNWA8753ET(MockAbstractDevice, NWA8753ET):
    """
    Mock interface for Agilent 34401A Digital Multimeter.
    """

    def __init__(self, *args, **kwargs):
        self.mocking = DM34401A

        MockAbstractDevice.__init__(self, *args, **kwargs)

    def _reset(self):
        MockAbstractDevice.write(self, 'Test', 2, done)


name = '8753ET'
implementation = MockNWA8753ET
