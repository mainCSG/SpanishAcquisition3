

from ..tools import quantity_unwrapped, quantity_wrapped
from ..abstract_device import AbstractDevice, AbstractSubdevice
from spacq.tool.box import Synchronized
from spacq.interface.resources import Resource
import logging
log = logging.getLogger(__name__)


"""
Physics Basel Low Noise/High Resolution DAC SP 927
Control the output voltages on all the ports.
"""


class Port(AbstractSubdevice):
    """
    An output port on the voltage source.
    """

    def _setup(self):
        AbstractSubdevice._setup(self)

        # Resources.
        read_write = ['voltage']
        for name in read_write:
            self.resources[name] = Resource(self, name, name)

        self.resources['voltage'].units = 'V'

    @Synchronized()
    def _connected(self):
        AbstractSubdevice._connected(self)

        # Turn on port
        output = self.device.ask_raw(
            '{0} ON\r\n'.format(self.num)).strip('\r\n')
        if output != 0:
            Warning("Device not connected!")
        # Gets current voltage in hex, convert it to volts and save the result
        result_hex = self.device.ask_raw(
            '{0} V?\r\n'.format(self.num)).strip('\r\n')
        if result_hex != "":
            result = self.hex_to_voltage(result_hex)
            self.currentVoltage = result
        else:
            self.currentVoltage = 0

    # Converts from hex to voltage (see user manual for more info)
    def hex_to_voltage(self, number):
        return int(number, 16)/838848 - 10

    # Converts from hex to voltage (see user manual for more info)
    def voltage_to_hex(self, voltage):
        # remove 0x that python adds automatically to hex
        return hex(int(round(((voltage+10)*838848), 0)))[2:]

    def __init__(self, device, num, *args, **kwargs):
        """
        Initialize the output port.
        device: The voltage source to which this Port belongs.
        num: The index of this port.
        """
        AbstractSubdevice.__init__(self, device, *args, **kwargs)
        self.num = num

    @property
    @quantity_wrapped('V')
    def voltage(self):
        return self.currentVoltage

    @voltage.setter
    @quantity_unwrapped('V')
    def voltage(self, value):
        """
        Set the voltage on this port, as a quantity in V.
        """
        value_hex = self.voltage_to_hex(value)
        output = self.device.ask_raw(
            '{0} {1}\r\n'.format(self.num, value_hex)).strip('\r\n')
        if output != 0:
            Warning("Voltage not properly set!")

        result_hex = self.device.ask_raw(
            '{0} V?\r\n'.format(self.num)).strip('\r\n')
        result = self.hex_to_voltage(result_hex)
        self.currentVoltage = result


class dacsp927(AbstractDevice):
    """
    Interface for the Physics Basel DAC SP 927 voltage source
    """

    def _setup(self):
        AbstractDevice._setup(self)

        self.ports = []
        for num in range(8):
            # Naming convention for DAC SP 927 goes 1 to 8
            port = Port(self, num+1, **self.port_settings)
            self.ports.append(port)
            self.subdevices['port{0}'.format(num+1)] = port

    def __init__(self, port_settings=None, *args, **kwargs):
        """
        Initialize the voltage source and all its ports.
        port_settings: A dictionary of values to give to each port upon creation.
        """

        if port_settings is None:
            self.port_settings = {}
        else:
            self.port_settings = port_settings

        AbstractDevice.__init__(self, *args, **kwargs)

    @Synchronized()
    def _connected(self):
        AbstractDevice._connected(self)
        # Add any initialization here. Careful: if you reconnect it will run this


name = 'dacsp927 Voltage Source'
implementation = dacsp927
