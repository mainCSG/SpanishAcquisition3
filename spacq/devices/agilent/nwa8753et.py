from ..tools import quantity_wrapped, quantity_unwrapped
from ..abstract_device import AbstractDevice
from spacq.tool.box import Synchronized
from spacq.interface.resources import Resource
import logging
log = logging.getLogger(__name__)


"""
Agilent 8753ET Network Analyzer

Current capabilities: Set CW frequency of network analyzer
ToDo: Could add sweep measurements (note: 8753ET locks GPIB while running sweep, so can't use it as a sweep and measure system)
"""


class NWA8753ET(AbstractDevice):
    """
    Interface for Agilent 8753ET
    """

    def _setup(self):
        AbstractDevice._setup(self)

        # Resources.
        read_only = ['marker']
        for name in read_only:
            self.resources[name] = Resource(self, name)

        read_write = ['cwFreq', 'power', 'markFreq']
        for name in read_write:
            self.resources[name] = Resource(self, name, name, name)

        self.resources['marker'].converter = float
        self.resources['cwFreq'].units = 'Hz'
        self.resources['power'].converter = float
        self.resources['markFreq'].units = 'Hz'

    @Synchronized()
    def _connected(self):
        AbstractDevice._connected(self)
        self.ask('opc?;pres')
        self.write('chan1')
        self.write('auxcoff')
        # For now, just set minimum power
        self.write('powe-20')

    @Synchronized()
    def reset(self):
        """
        Reset the device to its default state.
        """

        log.info('Resetting "{0}".'.format(self.name))
        self.write('*rst')

    @property
    @quantity_wrapped('Hz')
    def cwFreq(self):
        """
        The frequency of the networkAnalyzer output
        """

        return float(self.ask('cwfreq?'))

    @cwFreq.setter
    @quantity_unwrapped('Hz')
    def cwFreq(self, value):
        self.write('cwfreq{0}'.format(value))

    @property
    def power(self):
        """
        The power (in dB)
        """

        return float(self.ask('powe?'))

    @power.setter
    def power(self, value):
        self.write('powe{0}'.format(value))

    @property
    @Synchronized()
    def marker(self):
        """
        The value measured by the device at marker, as a quantity in dB.
        """

        self.status.append('Taking reading')

        try:
            log.debug('Getting reading.')
            result_raw = self.ask('OUTPMARK')
            result = float([x.strip() for x in result_raw.split(',')][0])
            log.debug('Got reading: {0}'.format(result))

            return result
        finally:
            self.status.pop()

    @property
    @quantity_wrapped('Hz')
    def markFreq(self):
        """
        The frequency of the marker in Hz
        """

        return float(self.ask('MARK1?'))

    @markFreq.setter
    @quantity_unwrapped('Hz')
    def markFreq(self, value):
        self.write('MARK1{0}'.format(value))


name = '8753ET'
implementation = NWA8753ET
