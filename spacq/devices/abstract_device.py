from packaging import version
from spacq.tool.box import Enum, Synchronized
from time import time
from threading import RLock
import logging
log = logging.getLogger(__name__)


"""
Hardware device abstraction interface.
"""


# PyVISA, PyVISA USB, telnet.
drivers = Enum(['pyvisa', 'pyvisa_usb', 'telnet'])


# Try to import all available drivers.
available_drivers = []

try:
    import telnetlib
    import socket
except ImportError:
    pass
else:
    available_drivers.append(drivers.telnet)

try:
    import pyvisa
except ImportError:
    pass
else:
    available_drivers.append(drivers.pyvisa)
    available_drivers.append(drivers.pyvisa_usb)


class DeviceNotFoundError(Exception):
    """
    Failure to connect to a device.
    """

    pass


class DeviceTimeout(Exception):
    """
    Timeout on action.
    """

    pass


class SuperDevice(object):
    def _setup(self):
        """
        Pre-connection setup.
        """

        self.name = self.__class__.__name__

        self.resources = {}
        self.subdevices = {}

    def _connected(self):
        """
        Post-connection setup.
        """

        # Recursively.
        for name, subdev in list(self.subdevices.items()):
            log.debug('Post-connection for subdevice "{0}".'.format(name))

            subdev._connected()


class AbstractDevice(SuperDevice):
    """
    A class for controlling devices which can be connected to either via Ethernet and (PyVISA or Telnet) or GPIB and Linux GPIB.
    """

    max_timeout = 15  # s

    def _setup(self):
        self.multi_command = None
        self.responses_expected = 0

        SuperDevice._setup(self)

        self.lock = RLock()

        self.status = []

    def __init__(self, ip_address=None, host_address=None, gpib_board=0, gpib_pad=None, gpib_sad=0,
                 usb_resource=None, autoconnect=True):
        """
        Ethernet (tcpip::<ip_address>::instr):
                ip_address: Address on which the device is listening on port 111.

        Telnet (<host_address>):
                host_address: String that list the IP address of the host.
                        Named this way to avoid issues with ip_address used for ethernet connections

        GPIB (gpib[gpib_board]::<gpib_pad>[::<gpib_sad>]::instr):
                gpib_board: GPIB board index. Defaults to 0.
                gpib_pad: Primary address of the device.
                gpib_sad: Secondary address of the device. Defaults to 0.

        USB (usb_resource):
                usb_resource: VISA resource of the form: USB[board]::<vendor>::<product>::<serial>[::<interface>]::RAW

        autoconnect: Connect to the device upon instantiation.
        """

        self._setup()

        log.info('Creating device "{0}".'.format(self.name))

        if ip_address is not None:
            if drivers.pyvisa in available_drivers:
                log.debug(
                    'Using PyVISA with ip_address="{0}".'.format(ip_address))
                self.driver = drivers.pyvisa
                self.connection_resource = {
                    'resource_name': 'TCPIP::{0}::INSTR'.format(ip_address),
                }
            else:
                raise NotImplementedError(
                    'PyVISA required, but not available.')

        elif host_address is not None:
            if drivers.telnet in available_drivers:
                log.debug(
                    'Using telnet with host_address="{0}".'.format(host_address))
                self.driver = drivers.telnet
                self.connection_resource = {
                    'host': '{0}'.format(host_address)
                }
            else:
                raise NotImplementedError(
                    'Telnetlib required, but not available.')

        elif gpib_pad is not None:
            if drivers.pyvisa in available_drivers:
                log.debug('Using PyVISA with gpib_board="{0}", gpib_pad="{1}", '
                          'gpib_sad="{2}".'.format(gpib_board, gpib_pad, gpib_sad))
                self.driver = drivers.pyvisa
                self.connection_resource = {
                    'resource_name': 'GPIB{0}::{1}::{2}::INSTR'.format(gpib_board, gpib_pad, gpib_sad),
                }
            else:
                raise NotImplementedError(
                    'Linux GPIB or PyVISA required, but not available.')
        elif usb_resource is not None:
            if drivers.pyvisa_usb in available_drivers:
                log.debug(
                    'Using PyVISA with usb_resource="{0}"'.format(usb_resource))
                self.driver = drivers.pyvisa_usb
                self.connection_resource = {
                    'resource_name': usb_resource,
                }
            else:
                raise NotImplementedError(
                    'PyVISA required, but not available.')
        else:
            raise ValueError(
                'Either an IP, Host Address, GPIB, or USB address must be specified.')

        if autoconnect:
            self.connect()

    def __repr__(self):
        return '<{0}>'.format(self.__class__.__name__)

    def connect(self):
        """
        Make a connection to the device.
        """

        log.info('Connecting to device "{0}" using {1} at "{2}".'.format(
            self.name, self.driver, self.connection_resource))

        if self.driver == drivers.pyvisa:
            try:
                rm = pyvisa.ResourceManager()
                self.device = rm.open_resource(**self.connection_resource)
            except pyvisa.VisaIOError as e:
                raise DeviceNotFoundError(
                    'Could not open device at "{0}".'.format(self.connection_resource), e)
        elif self.driver == drivers.telnet:
            self.device = telnetlib.Telnet(
                timeout=2, **self.connection_resource)

        elif self.driver == drivers.pyvisa_usb:
            try:
                rm = pyvisa.ResourceManager()
                self.device = rm.open_resource(**self.connection_resource)

            except pyvisa.VisaIOError as e:
                raise DeviceNotFoundError(
                    'Could not open device at "{0}".'.format(self.connection_resource), e)

        try:
            self._connected()
        except Exception as e:
            raise DeviceNotFoundError('Could not finish connection to device at "{0}".'.format(
                self.connection_resource), e)

    def multi_command_start(self):
        """
        Redirect further commands to a buffer.
        """

        log.debug(
            'Starting multi-command message for device "{0}"'.format(self.name))

        if self.driver not in [drivers.pyvisa]:
            raise NotImplementedError(
                'Unsupported driver: "{0}".'.format(self.driver))

        self.multi_command = []
        self.responses_expected = 0

    @Synchronized()
    def multi_command_stop(self):
        """
        Stop redirecting to a buffer, and send the buffered commands.

        Returns the results of queries if any were expected.
        """

        log.debug(
            'Stopping multi-command message for device "{0}"'.format(self.name))

        if self.multi_command is None:
            raise ValueError('Multi-command message not started.')
        elif not self.multi_command:
            # No commands.
            return []

        commands = self.multi_command
        # This ensures that write and ask will not buffer the real message.
        self.multi_command = None

        # Only commands not starting with "*" get a ":" prefix.
        commands = [cmd if cmd[0] == '*' else ':' + cmd for cmd in commands]
        message = ';'.join(commands)

        if self.responses_expected:
            result = self.ask(message)

            # FIXME: What if the response contains a meaningful ";" somewhere?
            return result.split(';', self.responses_expected - 1)
        else:
            self.write(message)

            return []

    @Synchronized()
    def write(self, message):
        """
        Write to the device.

        Supports multi-command.
        """

        if self.multi_command is not None:
            log.debug(
                'Writing to multi-command buffer for device "{0}": {1!r}'.format(self.name, message))

            self.multi_command.append(message)
            return

        log.debug('Writing to device "{0}": {1!r}'.format(self.name, message))

        if self.driver == drivers.pyvisa:
            try:
                self.device.write(message)
            except pyvisa.VisaIOError as e:
                if e.error_code == pyvisa.errors.VI_ERROR_TMO:
                    raise DeviceTimeout(e)
                else:
                    raise

        elif self.driver == drivers.telnet:
            try:
                self.device.write(message)
            except Exception:
                if e is socket.timeout:
                    raise DeviceTimeout(e)
                else:
                    raise

        elif self.driver == drivers.pyvisa_usb:
            # Send the message raw.
            self.device.write_raw(message)

    @Synchronized()
    def read_raw(self, chunk_size=512):
        """
        Read everything the device has to say and return it exactly.
        """

        log.debug('Reading from device "{0}".'.format(self.name))

        buf = ''

        if self.driver in [drivers.pyvisa, drivers.pyvisa_usb]:
            try:
                buf = self.device.read_raw()
            except pyvisa.VisaIOError as e:
                raise

        elif self.driver == drivers.telnet:
            try:
                buf = self.device.read_until('\r\n')
            except Exception as e:
                if e is socket.timeout:
                    raise DeviceTimeout(e)
                else:
                    raise

        log.debug('Read from device "{0}": {1!r}'.format(self.name, buf))

        return buf

    def read(self):
        """
        Read from the device, but strip terminating whitespace.
        """

        return self.read_raw().rstrip()

    @Synchronized()
    def ask_raw(self, message):
        """
        Write, then read_raw.
        """

        self.write(message)
        return self.read_raw()

    @Synchronized()
    def ask(self, message):
        """
        Write, then read.

        Supports multi-command.
        """

        self.write(message)

        if self.multi_command is None:
            return self.read()
        else:
            self.responses_expected += 1

    @Synchronized()
    def query(self, message):
        """
        Write then read using PyVisa's query command.
        """
        return self.device.query(message)

    def close(self):
        """
        Close the connection, if possible.
        """

        log.debug('Closing device: {0}'.format(self.name))

        if self.driver in [drivers.pyvisa, drivers.pyvisa_usb]:
            self.device.close()

    def find_resource(self, path):
        """
        Return a Resource given a resource path spec.

        eg. ('subdevice A', 'subdevice B', 'resource C') -> Resource
        """

        log.debug('Looking for resource {0}.'.format(path))

        if len(path) < 1:
            raise ValueError('No path provided.')

        # Keep track of the last device in the tree so far.
        dev = self
        # Keep track of the path so far.
        traversed = ()

        while len(path) > 1:
            try:
                dev = dev.subdevices[path[0]]
            except KeyError:
                raise ValueError(
                    'No subdevice "{0}" in {1}.'.format(path[0], traversed))

            traversed += path[:1]
            path = path[1:]

        try:
            return dev.resources[path[0]]
        except KeyError:
            raise ValueError(
                'No resource "{0}" in {1}.'.format(path[0], traversed))

    @property
    def idn(self):
        """
        Ask the device for identification.
        """

        if self.driver in [drivers.pyvisa]:
            return self.ask('*idn?')

    @property
    def opc(self):
        """
        Wait until the device is done.
        """

        end_time = time() + self.max_timeout

        while True:
            if self.driver in [drivers.pyvisa]:
                try:
                    self.ask('*opc?')
                except DeviceTimeout:
                    if time() > end_time:
                        raise
                else:
                    break


class AbstractSubdevice(SuperDevice):
    """
    A subdevice (eg. channel) of a hardware device.
    """

    def _setup(self):
        SuperDevice._setup(self)

        # Synchronized methods should use the device lock.
        self.lock = self.device.lock if self.device else None

    def __init__(self, device):
        self.device = device

        self._setup()
