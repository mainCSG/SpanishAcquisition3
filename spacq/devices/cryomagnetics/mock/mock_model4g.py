from ...mock.mock_abstract_device import MockAbstractDevice
from ..model4g import Model4G
import time

"""
Mock Model4G Power Supply
"""

class MockChannel(object):
	"""
	A mock channel for a mock 4G power supply.
	"""
	def __init__(self, device, channel, *args, **kwargs):
		self.mock_state = {}
		
		# Internals. (not read or write)
		self.mock_state['device'] = device
		self.mock_state['channel'] = channel
		self.mock_state['units'] = 'G'

		# Read-only.
		self.mock_state['magnet_current'] = 0
		self.mock_state['power_supply_current'] = 0
		
		# Read-write.
		self.mock_state['high_limit'] = 20
		self.mock_state['low_limit'] = 10
		self.mock_state['sweep'] = 'Standby'
		self.mock_state['persistent_switch_heater'] = 0
		self.mock_state['rate_0'] = 0.001
		self.mock_state['rate_1'] = 0.002
		self.mock_state['rate_2'] = 0.003
		self.mock_state['rate_3'] = 0.004
		self.mock_state['rate_4'] = 0.005
		
		self.mockdata = MockTimeData(self.mock_state['power_supply_current'],self.mock_state['power_supply_current'],1)

class MockData(object):
	'''
	Simulates the data that can be acquired from a sweep.
	It wraps a list that contains N datapoints in min to max, including min and max.
	Note that it is possible to have max < min. This will merely make the list go in
	descending order (such as if the 4G was sweeping down).
	'''
	
	def __init__(self, data_min, data_max, N):
		
		self.index = 0
		# We map a range [0,1,2,...,N] to the range [min,max].
		if N > 1:
			self.data_list = list(map( (lambda n:(data_max-data_min)*(float(n)/(N-1))+data_min), list(range(N))))
		elif N == 1:
			# if we have only 1 data point, then we just set it to min.
			self.data_list = [data_min]
			
	def GetDatum(self):
		
		result = self.data_list[self.index]

		#once the magnet sweeps to the last value, if one keeps retrieving values, it will stay
		#at the last value.
		if (self.index + 1) < len(self.data_list):
			self.index += 1
			

		return result
	
	def Reset(self):
		self.index = 0

class MockTimeData(object):
	'''
	Simulates the data that can be acquired from a sweep.
	It will return data as a linear function of time such that:
	t = 0 			<-> data_min
	t = time_to_max <-> data_max
	where t is the time since instantiation
	'''
	
	def __init__(self, data_min, data_max, time_to_max):
		
		self.t_init = time.time()

		def data_fn(t):
			if (t > time_to_max):
				return data_max
			else:
				return (data_max-data_min)*(float(t)/time_to_max)+data_min
			
		self.f = data_fn
			
	def GetDatum(self):
		result = self.f(time.time() - self.t_init)
		return result
	
	def Reset(self):
		self.t_init = time.time()

	
	
class MockModel4G(MockAbstractDevice, Model4G):
	"""
	Mock interface for Model 4G Power Supply.
	"""

	def __init__(self, *args, **kwargs):
		self.mocking = Model4G

		MockAbstractDevice.__init__(self, *args, **kwargs)
		
	def _reset(self):
		# Many other state properties are in the mock subdevice class MockChannel.
		
		self.mock_state['channels'] = [None] # There is no channel 0.
		for x in range(1, 3):
			self.mock_state['channels'].append(MockChannel(self,x))
		
		self.mock_state['active_channel'] = 1
				
	def write(self, message, result=None, done=False):
		if not done:
			cmd, args, query = self._split_message(message)
			
			mock_chan = self.mock_state['channels'][int(self.mock_state['active_channel'])]
						
			#should really take in kilogaussian and output in kilogaussian...
			multiplier = None
			output_unit = None
			if mock_chan.mock_state['units'] == 'G':
				multiplier = 1.
				output_unit = 'kG'
			elif mock_chan.mock_state['units'] == 'A':
				multiplier = 1.
				output_unit = 'A'
				

			
			if cmd[0] == 'ulim':
						if query:
							result = '{0} {1}'.format(mock_chan.mock_state['high_limit'] * multiplier, output_unit)
						else:
							if float(args) >= mock_chan.mock_state['low_limit']:
								mock_chan.mock_state['high_limit'] = float(args)
						done = True
			if cmd[0] == 'llim':
						if query:
							result = '{0} {1}'.format(mock_chan.mock_state['low_limit'] * multiplier, output_unit)
						else:
							if float(args) <= mock_chan.mock_state['high_limit']:
								mock_chan.mock_state['low_limit'] = float(args)
						done = True
			if cmd[0] == 'pshtr':
						if query:
							result = mock_chan.mock_state['persistent_switch_heater']
						else:
							if args == 'on':
								mock_chan.mock_state['persistent_switch_heater'] = 1
							elif args == 'off':
								mock_chan.mock_state['persistent_switch_heater'] = 0
						done = True
			elif cmd[0] == 'sweep':
				if query:
					result = mock_chan.mock_state['sweep']
				else:
					last_state = mock_chan.mock_state['sweep']
					
					#if sweep changes, then the data that will acquired is changed.
					if args == 'up' and last_state != 'up' : #up
						new_min = mock_chan.mock_state['power_supply_current']
						new_max = mock_chan.mock_state['high_limit']
						mock_chan.mockdata = MockTimeData(new_min,new_max,1)
					elif args == 'zero' and last_state != 'zero': #zero
						new_min = mock_chan.mock_state['power_supply_current']
						new_max = 0
						mock_chan.mockdata = MockTimeData(new_min,new_max,1)
					elif args == 'down' and last_state != 'down': #down
						new_min = mock_chan.mock_state['power_supply_current']
						new_max = mock_chan.mock_state['low_limit']
						mock_chan.mockdata = MockTimeData(new_min,new_max,1)
					elif args == 'pause' and last_state != 'paused': #paused
						new_min = new_max = mock_chan.mock_state['power_supply_current']
						mock_chan.mockdata = MockTimeData(new_min,new_max,1)
					
					if args == 'pause':
						mock_chan.mock_state['sweep'] = 'Pause'
					elif args == 'zero':
						mock_chan.mock_state['sweep'] = 'Sweeping to zero'
					else: 
						mock_chan.mock_state['sweep'] = 'Sweeping {0}'.format(args)
				done = True
			elif cmd[0] == 'chan':
				if query:
					result = self.mock_state['active_channel']
				else:
					self.mock_state['active_channel'] = args
				done = True
			elif cmd[0] == 'units':
				if query:
					result = mock_chan.mock_state['units']
				else:
					mock_chan.mock_state['units'] = args
				done = True
			elif cmd[0] == 'rate':
				if query:
					result = mock_chan.mock_state['rate_{0}'.format(args[0])]
				else:
					args = args.split()
					mock_chan.mock_state['rate_{0}'.format(args[0])] = args[1]
				done = True
			elif cmd[0] == 'imag':
				if query:
					if mock_chan.mock_state['persistent_switch_heater'] == 1:
						mock_chan.mock_state['power_supply_current'] = mock_chan.mockdata.GetDatum()
						mock_chan.mock_state['magnet_current'] = mock_chan.mock_state['power_supply_current']
						result = '{0} {1}'.format(mock_chan.mock_state['magnet_current'] * multiplier, output_unit)
					else:
						result = '{0} {1}'.format(mock_chan.mock_state['magnet_current'] * multiplier, output_unit)
				done = True
			elif cmd[0] == 'iout':
				if query:
					mock_chan.mock_state['power_supply_current'] = mock_chan.mockdata.GetDatum()
					result = '{0} {1}'.format(mock_chan.mock_state['power_supply_current'] * multiplier, output_unit)
				done = True
				
		# Perform rounding as defined by the precision of the actual device. Rounds to nearest Gaussian.
		if result is not None and ' kG' in str(result):
			rounded_number = round(float(result.replace(' kG','')), 3)
			result = '{0} {1}'.format(rounded_number, 'kG')
		else:
			pass #TODO: need to support rounding on amps.

		MockAbstractDevice.write(self, message, result, done)


name = 'Model 4G'
implementation = MockModel4G
