import logging
log = logging.getLogger(__name__)

from spacq.interface.resources import Resource
from spacq.tool.box import Synchronized

from ..abstract_device import AbstractDevice
from ..tools import quantity_wrapped, quantity_unwrapped

"""
Agilent 34401A Digital Multimeter

Obtain measurements from the multimeter.
"""


class SR830DSP(AbstractDevice):
	"""
	Interface for Stanford Research Systems SR830 DSP Lockin Amplifier

	NOTE: This implementation is currently very specific on its task, it could be made more flexible if desired
	"""

	#allowed_nplc = set([0.02, 0.2, 1.0, 10.0, 100.0])
	#allowed_auto_zero = set(['off', 'on', 'once'])

	min_amp = 0.00 # V (actual minimum is 0.004)
	max_amp = 5.000 # V

	min_freq = .001 # Hz
	max_freq = 102000 # Hz

	min_phase = -360 # degrees
	max_phase = 729 # degrees

	def _setup(self):
		AbstractDevice._setup(self)

		# Resources.
		#read_only = ['reading']
		#for name in read_only:
		#	self.resources[name] = Resource(self, name)

		read_write = ['reference_freq', 'reference_amplitude', 'reference_phase']
		for name in read_write:
			self.resources[name] = Resource(self, name, name)

		read_only = ['amplitude_x', 'amplitude_y', 'amplitude_R', 'angle_theta']
		for name in read_only:
			self.resources[name] = Resource(self, name, name, name, name)

		self.resources['reference_amplitude'].units = 'V'
		self.resources['reference_freq'].units = 'Hz'
		self.resources['amplitude_x'].units = 'V'
		self.resources['amplitude_y'].units = 'V'
		self.resources['amplitude_R'].units = 'V'

	@Synchronized()
	def _connected(self):
		AbstractDevice._connected(self)
		self.write('OUTX 1') # Sets interface of Lockin to GPIB
		self.write('FMOD 1') # Sets to use the internal oscillator

	@Synchronized()
	def reset(self):
		"""
		Reset the device to its default state.
		"""

		log.info('Resetting "{0}".'.format(self.name))
		self.write('*rst')

	@property
	@Synchronized()
	@quantity_wrapped('Hz')
	def reference_freq(self):
		"""
		The frequency of the internal oscillator
		"""

		return float(self.ask('FREQ?'))

	@reference_freq.setter
	@Synchronized()
	@quantity_unwrapped('Hz')
	def reference_freq(self, value):
		if value < self.min_freq or value > self.max_freq:
			raise ValueError('Value {0} not within the allowed bounds: {1} to {2}'.format(value, self.min_freq, self.max_freq))

		self.write('FREQ {0}'.format(value))

	@property
	def reference_phase(self):
		"""
		The phase of the internal oscillator
		"""

		return float(self.ask('PHAS?'))

	@reference_phase.setter
	def reference_phase(self, value):
		if float(value) < self.min_phase or float(value) > self.max_phase:
			raise ValueError('Value {0} not within the allowed bounds: {1} to {2}'.format(value, self.min_phase, self.max_phase))

		self.write('PHAS {0}'.format(value))

	@property
	@Synchronized()
	@quantity_wrapped('V')
	def reference_amplitude(self):
		"""
		The amplitude of the internal oscillator sine wave
		"""

		return float(self.ask('SLVL?'))

	@reference_amplitude.setter
	@Synchronized()
	@quantity_unwrapped('V')
	def reference_amplitude(self, value):
		if value < self.min_amp or value > self.max_amp:
			raise ValueError('Value {0} not within the allowed bounds: {1} to {2}'.format(value, self.min_amp, self.max_amp))

		self.write('SLVL {0}'.format(value))

	@property
	@Synchronized()
	@quantity_wrapped('V')
	def amplitude_x(self):
		"""
		The amplitude of the x component of lock-in signal
		"""

		return float(self.ask('OUTP? 1'))

	@property
	@Synchronized()
	@quantity_wrapped('V')
	def amplitude_y(self):
		"""
		The amplitude of the y component of lock-in signal
		"""

		return float(self.ask('OUTP? 2'))

	@property
	@Synchronized()
	@quantity_wrapped('V')
	def amplitude_R(self):
		"""
		The amplitude of the R magnitude of lock-in signal
		"""

		return float(self.ask('OUTP? 3'))

	@property
	@Synchronized()
	def angle_theta(self):
		"""
		The amplitude of the angle theta of lock-in signal
		"""

		return float(self.ask('OUTP? 4'))


name = 'SR830 DSP'
implementation = SR830DSP
