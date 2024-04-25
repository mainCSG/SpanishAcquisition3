from spacq.interface.units import Quantity
import string
from functools import wraps
import logging
from functools import reduce
log = logging.getLogger(__name__)


"""
Tools for working with hardware devices.
"""


def str_to_bool(value):
    """
    False and 'False' => False
    otherwise => True
    """

    return bool(value) and value.lower() != 'false'


def quantity_wrapped(units, multiplier=1.0):
    """
    A decorator for getters to wrap the plain device value into a quantity with a unit.
    """

    def wrap(f):
        @wraps(f)
        def wrapped(self):
            return Quantity(f(self) * multiplier, units)

        return wrapped

    return wrap


def quantity_unwrapped(units, multiplier=1.0):
    """
    A decorator for setters to extract the plain device value from the quantity.
    """

    def wrap(f):
        @wraps(f)
        def wrapped(self, value):
            value.assert_dimensions(units)

            return f(self, value.value * multiplier)

        return wrapped

    return wrap


def converted_quantity_unwrapped(units, multiplier=1.0):
    """
    A variation of quantity_unwrapped that extracts the value in the units provided, and then applies the multiplier
    if given.
    """

    def wrap(f):
        @wraps(f)
        def wrapped(self, value):
            value.assert_dimensions(units)

            # Perform conversion. Note that this is a bit of a trick. We must use a value of 1.0 because
            # normalization messes up for Quantities with 0 magnitude.
            new_value = Quantity(1.0, units)
            new_value += value
            new_value -= Quantity(1.0, units)

            return f(self, new_value.original_value * multiplier)

        return wrapped

    return wrap


def dynamic_quantity_wrapped(units_attr_string, multiplier=1.0):
    """
    A decorator for getters to wrap the plain device value into a quantity with a unit, where the unit
    is defined by an attribute extracted from the device.

    Note: Will work on a chain of dotted attributes.
    """

    def wrap(f):
        @wraps(f)
        def wrapped(self):

            units = reduce(getattr, units_attr_string.split('.'), self)
# units = getattr(self, units_attr_string)

            return Quantity(f(self) * multiplier, units)

        return wrapped

    return wrap


def dynamic_converted_quantity_unwrapped(units_attr_string, multiplier=1.0):
    """
    A variation of dynamic_quantity_unwrapped that will extract the units from an attribute of the device.
    """

    def wrap(f):
        @wraps(f)
        def wrapped(self, value):

            # units = getattr(self, units_attr_string)
            units = reduce(getattr, units_attr_string.split('.'), self)

            value.assert_dimensions(units)

            # Perform conversion. Note that this is a bit of a trick. We must use a value of 1.0 because
            # normalization messes up for Quantities with 0 magnitude.
            new_value = Quantity(1.0, units)
            new_value += value
            new_value -= Quantity(1.0, units)

            return f(self, new_value.original_value * multiplier)

        return wrapped

    return wrap


class BlockDataError(Exception):
    """
    Problem reading block data.
    """

    pass


class BlockData(object):
    """
    Utility methods for conversion between binary and 488.2 block data.
    """

    @staticmethod
    def to_block_data(data):
        """
        Packs binary data into 488.2 block data.

        As per section 7.7.6 of IEEE Std 488.2-1992.

        Note: Does not produce indefinitely-formatted block data.
        """

        log.debug('Converting to block data: {0!r}'.format(data))

        length = len(data)
        length_length = len(str(length))

        return '#{0}{1}{2}'.format(length_length, length, data)

    @staticmethod
    def from_block_data(block_data):
        """
        Extracts binary data from 488.2 block data.

        As per section 7.7.6 of IEEE Std 488.2-1992.
        """

        log.debug('Converting from block data: {0!r}'.format(block_data))

        # Must have at least "#0\n" or "#XX".
        if len(block_data) < 3:
            raise BlockDataError('Not enough data.')

        if block_data[0] != '#':
            raise BlockDataError(
                'Leading character is "{0}", not "#".'.format(block_data[0]))

        if block_data[1] == '0':
            log.debug('Indefinite format.')

            if block_data[-1] != '\n':
                raise BlockDataError(
                    'Final character is "{0}", not NL.'.format(block_data[-1]))

            return block_data[2:-1]
        else:
            log.debug('Definite format.')

            try:
                length_length = int(block_data[1])
            except ValueError:
                raise BlockDataError(
                    'Length length incorrectly specified: {0}'.format(block_data[1]))

            data_start = 2 + length_length

            if data_start > len(block_data):
                raise BlockDataError('Not enough data.')

            try:
                length = int(block_data[2:data_start])
            except ValueError:
                raise BlockDataError(
                    'Length incorrectly specified: {0}'.format(block_data[2:data_start]))

            data_end = data_start + length

            if data_end > len(block_data):
                raise BlockDataError('Not enough data.')
            elif data_end < len(block_data):
                if block_data[data_end:] != '\n':
                    log.warning('Extra data ignored: {0!r}'.format(
                        block_data[data_end:]))

            return block_data[data_start:data_end]


class BinaryEncoder(object):
    """
    Utility methods for dealing with encoding and decoding binary data.
    """

    @staticmethod
    def encode(msg):
        """
        Convert a string of hexadecimal digits to a byte string.
        """

        log.debug('Encoding to byte string: {0}'.format(msg))

        # Discard non-hexadecimal characters.
        msg_filtered = [x for x in msg if x in string.hexdigits]
        # Grab pairs.
        idxs = range(0, len(msg_filtered), 2)
        msg_paired = [''.join(msg_filtered[i:i+2]) for i in idxs]
        # Convert to bytes.
        msg_encoded = ''.join([chr(int(x, 16)) for x in msg_paired])

        log.debug('Encoded to: {0!r}'.format(msg_encoded))
        return msg_encoded

    @staticmethod
    def decode(msg, pair_size=2, pair_up=True):
        """
        Convert a byte string to a string of hexadecimal digits.
        """

        log.debug('Decoding from byte string: {0!r}'.format(msg))

        # Get the hex string for each byte.
        if type(msg) is bytes:
            # Convert bytes into hex and then merge them into pairs

            msg = msg.hex()
            msg_decoded = [msg[i] + msg[i+1]
                           for i in range(0, round(len(msg)), 2)]
        else:
            msg_decoded = ['{0:02x}'.format(ord(x)) for x in msg]

        if pair_up:
            idxs = range(0, len(msg_decoded), pair_size)
            msg_formatted = [''.join(msg_decoded[i:i+pair_size]) for i in idxs]

            result = ' '.join(msg_formatted)
        else:
            result = ''.join(msg_decoded)

        log.debug('Decoded to: {0}'.format(result))
        return result

    @staticmethod
    def length(msg):
        """
        Calculate the number of bytes an unencoded message takes up when encoded.
        """

        log.debug('Finding encoded length: {0}'.format(msg))

        result = len(BinaryEncoder.encode(msg))

        log.debug('Found encoded length: {0}'.format(result))

        return result
