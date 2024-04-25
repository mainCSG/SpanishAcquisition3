import logging
log = logging.getLogger(__name__)

from spacq.interface.resources import Resource
from spacq.tool.box import Synchronized

from ..abstract_device import AbstractDevice
from ..tools import quantity_wrapped, quantity_unwrapped

"""
Stanford Research Systems SG382 Signal Generator

Set output frequencies, modulation, etc. (not fully implemented)
"""


class SG382(AbstractDevice):
	"""
	Interface for Stanford Research Systems SG382
	"""

	allowedEnable = set(['off','on'])
	allowedModType = set(['0','1','2','3','4','5','6']) # AM, FM, Phase, Sweep, Pulse, Blank, IQ
	allowedModType = set(['AM','FM','Phase','Sweep','Pulse','Blank','IQ'])
	allowedModFunc = set(['0','1','2','3','4','5']) # Sine, Ramp, Triangle, Square, Noise, External
	allowedModFunc = set(['Sine','Ramp','Triangle','Square','Noise','External'])

	minBNCAmp = 0.0028 # Vpp (peak-to-peak)
	maxBNCAmp = 2.82 # Vpp
	minTypeNAmp = 2e-6 # Vpp
	maxTypeNAmp = 4.24 # Vpp

	minFreq = 1 # Hz
	maxFreq = 2e9 # Hz
	
	maxPhase = 180.0
	minPhase = -180.0

	def _setup(self):
		AbstractDevice._setup(self)

		# Resources.

		read_write = ['frequency', 'phase', 'BNCAmplitude', 'typeNAmplitude','modulationType','modulationEnabled','BNCEnable','typeNEnable','modulationFunction','FMDeviation','AMDepth']
		for name in read_write:
			self.resources[name] = Resource(self, name, name)

		#write_only = ['BNCEnable','typeNEnable']
		#for name in write_only:
		#	self.resources[name] = Resource(self, None, name)

		self.resources['frequency'].units = 'Hz'
		self.resources['BNCAmplitude'].units = 'V'
		self.resources['typeNAmplitude'].units = 'V'
		self.resources['FMDeviation'].units='Hz'
		self.resources['BNCEnable'].allowed_values = self.allowedEnable
		self.resources['typeNEnable'].allowed_values = self.allowedEnable
		self.resources['modulationEnabled'].allowed_values = self.allowedEnable
		self.resources['modulationType'].allowed_values = self.allowedModType
		self.resources['modulationFunction'].allowed_values = self.allowedModFunc

	@Synchronized()
	def _connected(self):
		AbstractDevice._connected(self)
		# Add any initialization here. Careful: if you reconnect it will run this

	@Synchronized()
	def reset(self):
		"""
		Reset the device to its default state.
		"""

		log.info('Resetting "{0}".'.format(self.name))
		self.write('*RST')

	@property
	@quantity_wrapped('Hz')
	def frequency(self):
		"""
		The output frequency of the signal generator
		"""

		return float(self.ask('FREQ?'))

	@frequency.setter
	@quantity_unwrapped('Hz')
	def frequency(self, value):
		if value < self.minFreq or value > self.maxFreq:
			raise ValueError('Value {0} not within the allowed bounds: {1} to {2}'.format(value, self.minFreq, self.maxFreq))

		self.write('FREQ {0}'.format(value))

	@property
	@quantity_wrapped('Hz')
	def FMDeviation(self):
		"""
		The amplitude of the frequency modulation
		"""

		return float(self.ask('FDEV?'))

	@FMDeviation.setter
	@quantity_unwrapped('Hz')
	def FMDeviation(self, value):
		self.write('FDEV {0}'.format(value))

	@property
	def AMDepth(self):
		"""
		The amplitude of amplitude modulation (as a percentage of total signal [eg, 90.0 is 90%]
		"""

		return float(self.ask('ADEP?'))

	@AMDepth.setter
	def AMDepth(self, value):
		self.write('ADEP {0}'.format(value))

	@property
	def phase(self):
		# The phase of the output, (in degrees but SpanishAcquisition uses no units for this TODO: fix this)
		return float(self.ask('PHAS?'))
		
	@phase.setter
	def phase(self,value):
		if float(value) < self.minPhase or float(value) > self.maxPhase:
			raise ValueError('Value {0} not within the allowed bounds: {1} to {2}'.format(value, self.minPhase, self.maxPhase))
			
		self.write('PHAS {0}'.format(value))
		
	@property
	@quantity_wrapped('V')
	def BNCAmplitude(self):
		# The amplitude of the output on the BNC output line (if enabled)
		# Currently using Vpp value, as Spanish Acquisition doesn't handle dBm currently (TODO: add dBm units)
		return float(self.ask('AMPL? VPP'))
		
	@BNCAmplitude.setter
	@quantity_unwrapped('V')
	def BNCAmplitude(self,value):
		if value < self.minBNCAmp or value > self.maxBNCAmp:
			raise ValueError('Value {0} not within the allowed bounds: {1} to {2}'.format(value, self.minBNCAmp, self.maxBNCAmp))
		
		self.write('AMPL {0} VPP'.format(value))
		
	@property
	@quantity_wrapped('V')
	def typeNAmplitude(self):
		# The amplitude of the output on the Type N output line (if enabled)
		# Currently using Vpp value, as Spanish Acquisition doesn't handle dBm currently (TODO: add dBm units)
		return float(self.ask('AMPR? VPP'))
		
	@typeNAmplitude.setter
	@quantity_unwrapped('V')
	def typeNAmplitude(self,value):
		if value < self.minTypeNAmp or value > self.maxTypeNAmp:
			raise ValueError('Value {0} not within the allowed bounds: {1} to {2}'.format(value, self.minTypeNAmp, self.maxTypeNAmp))
		
		self.write('AMPR {0} VPP'.format(value))
		
	@property
	def modulationType(self):
		# Coded setting of the modulation type (eg, 1 = Amplitude Modulation)
		result = self.ask('TYPE?')
		if result == '0':
			return 'AM'
		elif result == '1':
			return 'FM'
		elif result == '2':
			return 'Phase'
		elif result == '3':
			return 'Sweep'
		elif result == '4':
			return 'Pulse'
		elif result == '5':
			return 'Blank'
		elif result == '6':
			return 'IQ'
		
	@modulationType.setter
	def modulationType(self,value):
		if value not in self.allowedModType:
			raise ValueError('Invalid Modulation Type: {0}'.format(value))
		
		if value == 'AM':
			outCode = 0
		elif value == 'FM':
			outCode = 1
		elif value == 'Phase':
			outCode = 2
		elif value == 'Sweep':
			outCode = 3
		elif value == 'Pulse':
			outCode = 4
		elif value == 'Blank':
			outCode = 5
		elif value == 'IQ':
			outCode = 6

		self.write('TYPE {0}'.format(outCode))

	@property
	def modulationFunction(self):
		# Coded setting of the modulation type (eg, 1 = Amplitude Modulation)
		result = self.ask('MFNC?')
		if result == '0':
			return 'Sine'
		elif result == '1':
			return 'Ramp'
		elif result == '2':
			return 'Triangle'
		elif result == '3':
			return 'Square'
		elif result == '4':
			return 'Noise'
		elif result == '5':
			return 'External'
		
	@modulationFunction.setter
	def modulationFunction(self,value):
		if value not in self.allowedModFunc:
			raise ValueError('Invalid Modulation Function: {0}'.format(value))
		
		if value == 'Sine':
			outCode = 0
		elif value == 'Ramp':
			outCode = 1
		elif value == 'Triangle':
			outCode = 2
		elif value == 'Square':
			outCode = 3
		elif value == 'Noise':
			outCode = 4
		elif value == 'External':
			outCode = 5

		self.write('MFNC {0}'.format(outCode))
		
	@property
	def modulationEnabled(self):
		# Turn on/off modulation of signal
		result = self.ask('MODL?')
		if result == '0':
			return 'off'
		elif result == '1':
			return 'on'
	
	@modulationEnabled.setter
	def modulationEnabled(self,value):
		if value not in self.allowedEnable:
			raise ValueError('Invalid modulation enable setting: {0}'.format(value))
			
		if value == 'off':
			outCode = 0
		elif value == 'on':
			outCode = 1

		self.write('MODL {0}'.format(outCode))
		
	@property
	def BNCEnable(self):
		# Turn on/off the BNC output (it is automatically off above 62.5 MHz)
		result = self.ask('ENBL?')
		if result == '0':
			return 'off'
		elif result == '1':
			return 'on'
	
	@BNCEnable.setter
	def BNCEnable(self,value):
		if value not in self.allowedEnable:
			raise ValueError('Invalid BNC enable setting: {0}'.format(value))
			
		if value == 'off':
			outCode = 0
		elif value == 'on':
			outCode = 1

		self.write('ENBL {0}'.format(outCode))
		
	@property
	def typeNEnable(self):
		# Turn on/off the type-N output
		result = self.ask('ENBR?')
		if result == '0':
			return 'off'
		elif result == '1':
			return 'on'
	
	@typeNEnable.setter
	def typeNEnable(self,value):
		if value not in self.allowedEnable:
			raise ValueError('Invalid type-N enable setting: {0}'.format(value))
			
		if value == 'off':
			outCode = 0
		elif value == 'on':
			outCode = 1

		self.write('ENBR {0}'.format(outCode))

name = 'SG382 Signal Generator'
implementation = SG382
