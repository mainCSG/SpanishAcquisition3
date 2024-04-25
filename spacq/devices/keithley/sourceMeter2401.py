from ..tools import quantity_unwrapped
from ..tools import quantity_wrapped
from ..abstract_device import AbstractDevice
from spacq.tool.box import Synchronized
from spacq.interface.resources import Resource
import logging
log = logging.getLogger(__name__)


"""
Keithley 2401 SourceMeasure Unit
Apply voltage/current bias and obtain measurements.
"""


class sm2401(AbstractDevice):
    """
    Interface for Keithley 2401
    Note: Limited implementation, many features are not included
    """

    #allowedSourceType = set(['Voltage','Current'])
    #allowedSenseType = set(['Voltage','Current'])
    allowedOutput = set(['on', 'off'])

    def _setup(self):
        AbstractDevice._setup(self)

        # Resources.
        read_only = ['voltageIn', 'currentIn']
        for name in read_only:
            self.resources[name] = Resource(self, name)

        #read_write = ['voltageOut', 'currentOut','sourceType','senseType']
        read_write = ['voltageOut', 'currentOut', 'output']
        for name in read_write:
            self.resources[name] = Resource(self, name, name)

        self.resources['voltageIn'].units = 'V'
        self.resources['voltageOut'].units = 'V'
        self.resources['currentIn'].units = 'A'
        self.resources['currentOut'].units = 'A'
        self.resources['output'].allowed_values = self.allowedOutput
        self.currOutputState = -1
        self.currentOutputCurrent = -88
        self.currentOutputVoltage = -88
        #self.resources['sourceType'].allowed_values = self.allowedSourceType
        #self.resources['senseType'].allowed_values = self.allowedSenseType

    @Synchronized()
    def _connected(self):
        AbstractDevice._connected(self)

        # self.write('configure:voltage:dc')
        # TODO: Create a default setup?

        # Get output on/off state to determine if we can ask certain things
        self.currOutputState = int(self.ask('OUTP?'))

    @Synchronized()
    def reset(self):
        """
        Reset the device to its default state.
        """

        log.info('Resetting "{0}".'.format(self.name))
        self.write('*rst')

    @property
    def output(self):
        # Coded setting of the output on/off (1 = on, 0 = off)
        result = self.ask('OUTP?')
        if result == '0':
            self.currOutputState = 0
            return 'off'
        elif result == '1':
            self.currOutputState = 1
            return 'on'

    @output.setter
    def output(self, value):
        if value not in self.allowedOutput:
            raise ValueError('Invalid Output State: {0}'.format(value))

        if value == 'off':
            outCode = 0
            self.currOutputState = 0
        elif value == 'on':
            outCode = 1
            self.currOutputState = 1

        self.write('OUTP {0}'.format(outCode))

    @property
    @quantity_wrapped('V')
    def voltageIn(self):
        if self.currOutputState:
            outString = self.ask('READ?').decode()
            # The output returns a 5 number string, first number is voltage, second is current, third is res
            return float(outString.split(',')[0])
        else:
            return -999

    @property
    @quantity_wrapped('A')
    def currentIn(self):
        if self.currOutputState:
            outString = self.ask('READ?').decode()
            return float(outString.split(',')[1])
        else:
            return -999

    @property
    @quantity_wrapped('V')
    def voltageOut(self):
        if self.currOutputState:
            return float(self.ask('SOUR:VOLT?'))
        else:
            return self.currentOutputVoltage

    @voltageOut.setter
    @quantity_unwrapped('V')
    def voltageOut(self, value):
        self.write('SOUR:FUNC VOLT')
        self.write('SOUR:VOLT:LEV {0}'.format(value))
        self.currentOutputVoltage = value

    @property
    @quantity_wrapped('A')
    def currentOut(self):
        if self.currOutputState:
            return float(self.ask('SOUR:CURR?'))
        else:
            return self.currentOutputCurrent

    @currentOut.setter
    @quantity_unwrapped('A')
    def currentOut(self, value):
        #self.write('SOUR:FUNC CURR')
        self.write('SOUR:CURR:LEV {0}'.format(value))
        self.currentOutputCurrent = value


name = 'sourceMeter 2401'
implementation = sm2401
