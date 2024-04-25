import logging
log = logging.getLogger(__name__)

from spacq.interface.resources import Resource
from spacq.tool.box import Synchronized
from spacq.interface.units import Quantity
from time import sleep
from functools import wraps

from ..abstract_device import AbstractDevice, AbstractSubdevice
from ..tools import quantity_wrapped, quantity_unwrapped
from ..tools import dynamic_quantity_wrapped, dynamic_converted_quantity_unwrapped


"""
Cryomagnetics model 4G Device
"""

class Channel(AbstractSubdevice):
    """
    Interface for a channel on the Model4G
    """
    

    allowed_switch_heater = set(['on','off'])
    allowed_heater_wait_mode = set(['on','off'])
    allowed_sweep = set(['up','zero','down', 'pause'])
    allowed_sync = set(['start','stop'])
    allowed_energysave_mode = set([0,1,2,3,4])
    allowed_units = set(['kG','A'])
    
    def _setup(self):
        AbstractSubdevice._setup(self)
        
        # Resources.
        
        read_only = ['magnet_current','power_supply_current']
        for name in read_only:
            self.resources[name] = Resource(self, name)
            
        read_write = ['persistent_switch_heater', 'high_limit','low_limit','sweep',
                        'rate_0','rate_1','rate_2','rate_3','rate_4', 'virt_sync_currents', 'virt_imag', 'virt_iout',
                        'virt_imag_sweep_to','virt_iout_sweep_to','virt_energysave_mode', 'virt_heater_wait_mode'
                        ,'virt_sweep_sleep', 'units']
        for name in read_write:
            self.resources[name] = Resource(self, name, name)
            
        # Resources with their units controlled by self._units.        
        self.dynamic_unit_resources = ['virt_imag_sweep_to','virt_iout_sweep_to','virt_imag','virt_iout','magnet_current',
                                  'power_supply_current','high_limit','low_limit' ]
        for name in self.dynamic_unit_resources:
            self.resources[name].units = self._units

        self.resources['virt_sweep_sleep'].units = 's'
        for x in range(5):
            self.resources['rate_{0}'.format(x)].units = 'A.s-1'
        
        self.resources['virt_heater_wait_mode'].allowed_values = self.allowed_heater_wait_mode
        self.resources['virt_energysave_mode'].allowed_values = self.allowed_energysave_mode
        self.resources['virt_energysave_mode'].converter = int
        self.resources['persistent_switch_heater'].allowed_values = self.allowed_switch_heater
        self.resources['sweep'].allowed_values = self.allowed_sweep
        self.resources['virt_sync_currents'].allowed_values = self.allowed_sync
        self.resources['units'].allowed_values = self.allowed_units
                
    def __init__(self, device, channel, *args, **kwargs):
        self.channel = channel
        
        # internal attributes used for virtual features not present in actual device.
        self._units = 'kG' # default units.
        self._energysave_mode = 0
        self._iout_target = None
        self._imag_target = None
        self._heater_wait_mode = 'on'
        self._sweep_sleep = 1.
        
        AbstractSubdevice.__init__(self, device, *args, **kwargs)

    def _connected(self):
        # Initializations requiring GPIB.        
        self.units = self._units
        self._iout_target = self.power_supply_current.original_value
        self._imag_target = self.magnet_current.original_value

    def _wait_for_sweep(self):
        '''
        This is an internal function that loops until a sweep is complete.
        This allows some of the virtual features to wait until a sweep is complete before performing other commands.
        '''
        
        for i in range(0,2):
            current_sweep = self.sweep
            if current_sweep == 'Sweeping up':
                while current_sweep != 'Pause' and self.power_supply_current != self.high_limit:
                    sleep(0.1) #give the GPIB some breathing space.
                    current_sweep = self.sweep
            elif current_sweep == 'Sweeping to zero':
                while current_sweep != 'Pause' and self.power_supply_current != Quantity(0,self._units):
                    sleep(0.1)
                    current_sweep = self.sweep
            elif current_sweep == 'Sweeping down':
                while current_sweep != 'Pause' and self.power_supply_current != self.low_limit:
                    sleep(0.1)
                    current_sweep = self.sweep
            if i == 0 and self.virt_sweep_sleep.value != 0:
                sleep(self.virt_sweep_sleep.value) # we sleep, then check once more to ensure the sweep has stabilized.
    
    
    class _set_channel(object):
        """
        A decorator which prefixes a method with a setting of the channel.
        Note: Usually, this decorator should be wrapped underneath the @Synchronized() method
        """
        @staticmethod
        def __call__(f):
            @wraps(f)
            def decorated(self, *args, **kwargs):
                
                # Set channel here.
                if self.device.active_channel_store is not self.channel:
                    self.device.active_channel = self.channel
                                
                return f(self, *args, **kwargs)
    
            return decorated
            
    
    # Low-level Direct Controls. ####################################################################################
    

    @property
    @Synchronized()
    @dynamic_quantity_wrapped('_units')
    @_set_channel()
    def high_limit(self):
        """
        The upper limit on the magnetic current
        """
        response = self.device.ask('ulim?')    
        stripped_response =  Quantity.from_string(response)[0]
        return stripped_response

    @high_limit.setter
    @Synchronized()
    @dynamic_converted_quantity_unwrapped('_units')
    @_set_channel()
    def high_limit(self,value):
        self.device.write('ulim {0}'.format(value))
    
    @property
    @Synchronized()
    @dynamic_quantity_wrapped('_units')
    @_set_channel()
    def low_limit(self):
        """
        The lower limit on the magnetic current
        """
        response = self.device.ask('llim?')
        stripped_response =  Quantity.from_string(response)[0]
        return stripped_response
    
    @low_limit.setter
    @Synchronized()
    @dynamic_converted_quantity_unwrapped('_units')
    @_set_channel()
    def low_limit(self,value):
        
        self.device.write('llim {0}'.format(value))
    
    @property
    @Synchronized()
    @dynamic_quantity_wrapped('_units')
    @_set_channel()
    def magnet_current(self):
        """
        This is the persistent magnet current setting
        """
        response = self.device.ask('imag?')    
        stripped_response =  Quantity.from_string(response)[0]
        return stripped_response
        
    @property
    @Synchronized()
    @_set_channel()
    def persistent_switch_heater(self):
        """
        The persistent switch heater
        """
        response = float(self.device.ask('pshtr?'))
        
        # when getting from the device immediately after a set, the power supply returns a 2 if it has not fully
        # changed
        while response == 2:
            sleep(0.5)
            response = float(self.device.ask('pshtr?'))
            

        response_dict = {0:'off', 1:'on'}
        
        return response_dict[response]
    
    @persistent_switch_heater.setter
    @Synchronized()
    @_set_channel()
    def persistent_switch_heater(self,value):
        
        if value not in self.allowed_switch_heater:
            raise ValueError('Invalid heater switch value: {0}'.format(value))
        
        # don't allow the heater switch to go on if currents not synced
        if self.virt_sync_currents != 'synced' and value == 'on':
            raise ValueError('Currents are not synced in channel {0}.'.format(self.channel))
                
        self.device.write('pshtr {0}'.format(value))
        
        # Give the heaters time to warm up, if desired.
        if self.virt_heater_wait_mode == 'on':
            sleep(1)
        
    @property
    @Synchronized()
    @dynamic_quantity_wrapped('_units')
    @_set_channel()
    def power_supply_current(self):
        """
        The power supply output current
        """
        response = self.device.ask('iout?')    
        stripped_response =  Quantity.from_string(response)[0]
        return stripped_response    
            
    @quantity_wrapped('A')
    @Synchronized()
    @_set_channel()
    def ranges(self,range_id):
        '''
        Used to grab the range for a given range id.
        '''
        if range_id != 0:
            lower = self.device.ask('range? {0}'.format(range_id-1))
        else:
            lower = 0
            
        upper = self.device.ask('range? {0}'.format(range_id))
        
        return ('{0} to {1}'.format(lower,upper))
    
    @property
    @quantity_wrapped('A.s-1')
    @Synchronized()
    @_set_channel()
    def rate_0(self):
        """
        A rate for a rate range
        """
        return float(self.device.ask('rate? 0'))
    
    @rate_0.setter
    @quantity_unwrapped('A.s-1')
    @Synchronized()
    @_set_channel()
    def rate_0(self,value):

        self.device.write('rate 0 {0}'.format(value))
                                
    @property
    @quantity_wrapped('A.s-1')
    @Synchronized()
    @_set_channel()
    def rate_1(self):
        """
        A rate for a rate range
        """
        return float(self.device.ask('rate? 1'))
    
    @rate_1.setter
    @quantity_unwrapped('A.s-1')
    @Synchronized()
    @_set_channel()
    def rate_1(self,value):

        self.device.write('rate 1 {0}'.format(value))

    @property
    @quantity_wrapped('A.s-1')
    @Synchronized()
    @_set_channel()
    def rate_2(self):
        """
        A rate for a rate range
        """
        return float(self.device.ask('rate? 2'))
    
    @rate_2.setter
    @quantity_unwrapped('A.s-1')
    @Synchronized()
    @_set_channel()
    def rate_2(self,value):
    
        self.device.write('rate 2 {0}'.format(value))                
    
    @property
    @quantity_wrapped('A.s-1')
    @Synchronized()
    @_set_channel()
    def rate_3(self):
        """
        A rate for a rate range
        """
    
        return float(self.device.ask('rate? 3'))
    
    @rate_3.setter
    @quantity_unwrapped('A.s-1')
    @Synchronized()
    @_set_channel()
    def rate_3(self,value):
    
        self.device.write('rate 3 {0}'.format(value))
    
    @property
    @quantity_wrapped('A.s-1')
    @Synchronized()
    @_set_channel()
    def rate_4(self):
        """
        A rate for a rate range
        """
        return float(self.device.ask('rate? 4'))
    
    @rate_4.setter
    @quantity_unwrapped('A.s-1')
    @Synchronized()
    @_set_channel()
    def rate_4(self,value):

        self.device.write('rate 4 {0}'.format(value))
        
    @property
    @Synchronized()
    @_set_channel()
    def sweep(self):
        """
        The sweeper control.
        """
        response = str(self.device.ask('sweep?'))
        return response
    
    @sweep.setter
    @Synchronized()
    @_set_channel()
    def sweep(self,value):
            
        if value not in self.allowed_sweep:
            raise ValueError('Invalid sweep value: {0}'.format(value))
        
        self.device.write('sweep {0}'.format(value))
        
    @property
    @Synchronized()
    @_set_channel()
    def units(self):
        """
        Get current units of the device.
        """
        self.device.active_channel = self.channel
        
        response = self.device.ask('units?').decode()
        
        # We perform a conversion between the GUI and the device with this dict.
        read_dict = {'G':'kG','A':'A'}
        
        # if the device is different from the local copy, then we convert device to local copy.
        if self._units != read_dict[response]:
            self.units = self._units
            
        return read_dict[response]
            
    
    @units.setter
    @Synchronized()
    @_set_channel()
    def units(self,value):
        """
        Set current units.
        """
        if value not in self.allowed_units:
            raise ValueError('Invalid units: {0}'.format(value))
        
        # Perform a conversion between the GUI and the device with this dict.
        write_dict = {'kG':'G','A':'A'}
        
        self.device.write('units {0}'.format(write_dict[value]))
        
        # Change our locally stored copy to the new user-defined units.
        self._units = value
        
        # Change all the appropriate resources' units
        for name in self.dynamic_unit_resources:
            self.resources[name].units = self._units
        
        
    # High-level Virtual Controls. ##################################################################################
        
                            
    @property
    def virt_energysave_mode(self):
        '''
        If enabled: after incrementing virt_imag_sweep_to, the magnet will go into persistent mode, and then
        start a sweep of the power supply current to 0
        '''
        return self._energysave_mode
    
    @virt_energysave_mode.setter
    def virt_energysave_mode(self, value):
        '''
        If enabled: after incrementing virt_imag_sweep_to, the magnet will go into persistent mode, and then
        start a sweep of the power supply current to 0
        '''
        self._energysave_mode = value
        
    @property
    @Synchronized()
    @dynamic_quantity_wrapped('_units')
    def virt_imag(self):
        '''
        Getter:
        Simply returns the magnet current.
        Setter:
        This wraps virt_iout_sweep_to with current syncing, as well as optional energy saving.
        '''
        return self.magnet_current.original_value
        
    @virt_imag.setter
    @dynamic_converted_quantity_unwrapped('_units')
    def virt_imag(self, value):

        if self.virt_energysave_mode == 4:
            self.virt_sync_currents = 'start'
            self._wait_for_sweep()
            self.persistent_switch_heater = 'on'
            self.virt_iout = Quantity(value,self._units)
            self.persistent_switch_heater = 'off'
            self.sweep = 'zero'
        elif self.virt_energysave_mode == 3:
            self.virt_sync_currents = 'start'
            self._wait_for_sweep()
            self.device.virt_both_persistent_switch_heaters = 'on'
            self.virt_iout = Quantity(value,self._units)
            self.device.virt_both_persistent_switch_heaters = 'off'
            self.sweep = 'zero'
        elif self.virt_energysave_mode == 2:
            self.persistent_switch_heater = 'on'
            self.virt_iout = Quantity(value,self._units)
            self.persistent_switch_heater = 'off'
        elif self.virt_energysave_mode == 1:
            self.device.virt_both_persistent_switch_heaters = 'on'
            self.virt_iout = Quantity(value,self._units)
            self.device.virt_both_persistent_switch_heaters = 'off'
        elif self.virt_energysave_mode == 0:
            if self.persistent_switch_heater != 'on':
                raise ValueError('Heater switch is not on in channel {0}.'.format(self.channel))
            self.virt_iout = Quantity(value, self._units)
            
    @property
    @dynamic_quantity_wrapped('_units')
    def virt_imag_sweep_to(self):
        '''
        Getter:
        Simply returns the magnet current.
        Setter:
        This wraps virt_iout_sweep_to with current syncing, as well as optional energy saving.
        '''
        return self._imag_target
       
    @virt_imag_sweep_to.setter
    @dynamic_converted_quantity_unwrapped('_units')
    def virt_imag_sweep_to(self, value):
        
        if self.persistent_switch_heater != 'on':
            self.persistent_switch_heater = 'on'
        
        self.virt_iout_sweep_to = Quantity(value, self._units)
        
        if self._units == 'kG':
            self._imag_target = round(value,3) #round to the nearest Gaussian.
        else:
            self._imag_target = value #TODO: need to support rounding on amps.
            
    @property
    @Synchronized()
    @dynamic_quantity_wrapped('_units')
    def virt_iout(self):
        """
        Getter:
        Simply returns the power supply current.
        Setter:
        Used to increment the output power supply current using lower level controls.
        
        Note: power_supply_current is already wrapped with units, so no need to wrap this function.
        """            
        return self.power_supply_current.original_value
            
    @virt_iout.setter
    @dynamic_converted_quantity_unwrapped('_units')
    def virt_iout(self, value):

        # determine whether to set the hilim or lolim for increment, then sweep
        if value == 0:
            self.sweep = 'zero'
        elif self.power_supply_current.value < value:
            
            if self.low_limit > Quantity(value, self._units):
                self.low_limit = Quantity(value, self._units)
                
            self.high_limit = Quantity(value, self._units)
            self.sweep = 'up'
            
        elif self.power_supply_current.value > value:
            
            if self.high_limit < Quantity(value, self._units):
                self.high_limit = Quantity(value, self._units)
                
            self.low_limit = Quantity(value, self._units)
            self.sweep = 'down'
        
        self._wait_for_sweep()



    @property
    @Synchronized()
    @dynamic_quantity_wrapped('_units')
    def virt_iout_sweep_to(self):
        """
        Getter:
        Simply returns the power supply current.
        Setter:
        Used to increment the output power supply current using lower level controls.
        
        Note: power_supply_current is already wrapped with units, so no need to wrap this function.
        """
        return self._iout_target
    
    @virt_iout_sweep_to.setter
    @dynamic_converted_quantity_unwrapped('_units')
    def virt_iout_sweep_to(self, value):
        
        # determine whether to set the hilim or lolim for increment, then sweep
        if value == 0:
            self.sweep = 'zero'
        elif self.power_supply_current.value < value:
            
            if self.low_limit > Quantity(value, self._units):
                self.low_limit = Quantity(value, self._units) #we put the low limit to zero
                
            self.high_limit = Quantity(value, self._units)
            self.sweep = 'up'
            
        elif self.power_supply_current.value > value:
            
            if self.high_limit < Quantity(value, self._units):
                self.high_limit = Quantity(value, self._units)
                
            self.low_limit = Quantity(value, self._units)
            self.sweep = 'down'
            
            
        if self._units == 'kG':
            self._iout_target = round(value,3)
        else:
            self._iout_target = value #TODO: need to support rounding on amps.
            
    @property
    @quantity_wrapped('s')
    def virt_sweep_sleep(self):
        """
        Debugging purposes, although potentially the basis for a feature in the future.
        Changes the sleep period in _wait_for_sweep after detecting the sweep is done.
        """
        return self._sweep_sleep
    
    @virt_sweep_sleep.setter
    @quantity_unwrapped('s')
    def virt_sweep_sleep(self,value):
        
        self._sweep_sleep = value
        
    @property
    @Synchronized()
    def virt_sync_currents(self):
        """
        Used to sync the currents. Note this is a virtual feature not present in the actual device.
        """
        if self.magnet_current == self.power_supply_current:
            return 'synced'
        else:
            return 'not synced'

    @virt_sync_currents.setter
    @Synchronized()
    def virt_sync_currents(self, value):
        
        if value == 'start':
            self.virt_iout_sweep_to = self.magnet_current
        elif value == 'stop':
            self.sweep = 'pause'
            
    @property
    def virt_heater_wait_mode(self):
        
        return self._heater_wait_mode
    
    @virt_heater_wait_mode.setter
    def virt_heater_wait_mode(self, value):
        
        if value not in self.allowed_heater_wait_mode:
            raise ValueError('Invalid heater wait mode value: {0}'.format(value))
        
        self._heater_wait_mode = value


class Model4G(AbstractDevice):
    """
    Interface for Model 4G
    """
    allowed_active_channel = set([1,2])
    allowed_both_heaters = set(['on','off'])
    allowed_both_units = set(['kG','A'])
    
    @property
    def _gui_setup(self):
        try:
            from .gui.model4g import Model4GFrontPanelDialog

            return Model4GFrontPanelDialog
        except ImportError as e:
            log.debug('Could not load GUI setup for device "{0}": {1}'.format(self.name, str(e)))

            return None

    def _setup(self):
        AbstractDevice._setup(self)
        
        # Channel subdevices.
        self.channels = [None] # There is no channel 0.
        for chan_num in range(1, 3):
            channel = Channel(self,chan_num)
            self.subdevices['channel{0}'.format(chan_num)] = channel
            # this list is useful as it is actually ordered, as opposed to the dict above.
            self.channels.append(channel)
            
        #This saves the last channel set to the device for programming purposes...its a way of minimizing
        #calls to the device.
        self.active_channel_store = None

        # Resources.
        
        read_write = ['active_channel', 'virt_both_persistent_switch_heaters', 'virt_both_units']
        for name in read_write:
            self.resources[name] = Resource(self, name, name)
        
        self.resources['active_channel'].allowed_values = self.allowed_active_channel
        self.resources['active_channel'].converter = int
        self.resources['virt_both_persistent_switch_heaters'].allowed_values = self.allowed_both_heaters
        self.resources['virt_both_units'].allowed_values = self.allowed_both_units
                        
    @Synchronized()
    def _connected(self):
        AbstractDevice._connected(self)
        
        # Start off with active channel as 1. Doing this to initialize active_channel_store.
        self.active_channel = 1
        
        
    @Synchronized()
    def reset(self):
        """
        Reset the device to its default state.
        """

        log.info('Resetting "{0}".'.format(self.name))
        self.write('*rst')

        #TODO: test if the *rst actually DOES do something to the magnet controller.
        
        self.virt_both_units = 'kG'
        
        for channel in [1,2]:
            
            subdev = self.channels[channel]
            
            subdev.virt_energysave_mode = 0
            subdev.virt_sync_currents = 'start'
            subdev._wait_for_sweep()
            subdev.persistent_switch_heater = 'on'
            subdev.virt_imag = Quantity('0 kG')
            
            subdev.low_limit = Quantity('0 kG')
            subdev.high_limit = Quantity('0 kG')
            
            subdev.virt_imag_sweep_to = Quantity('0 kG')
            subdev.virt_iout_sweep_to = Quantity('0 kG')
            subdev.persistent_switch_heater = 'off'
            
        #ensure the defaults set appropriately for both channels
        for channel in [1,2]:
            subdev = self.channels[channel]
            
            resource_check_dict = { subdev.virt_energysave_mode:0, 
                                    subdev.virt_sync_currents:'synced',
                                    self.virt_both_units:'kG',
                                    subdev.power_supply_current:Quantity('0 kG'),
                                    subdev.magnet_current:Quantity('0 kG'),
                                    subdev.persistent_switch_heater:'off',
                                    subdev.high_limit:Quantity('0 kG'),
                                    subdev.low_limit:Quantity('0 kG'),
                                    subdev.virt_imag_sweep_to:Quantity('0 kG'),
                                    subdev.virt_iout_sweep_to:Quantity('0 kG')
                                    }
            
            for resource, value in list(resource_check_dict.items()):
                if resource != value:
                    raise ValueError('A resource with value {0} did not set to its default value of {1}'.format(resource, value))


    @property
    def active_channel(self):
        """
        The active device channel.
        """
        return float(self.ask('chan?'))
    
    @active_channel.setter
    def active_channel(self,value):
        if value not in self.allowed_active_channel:
            raise ValueError('Invalid channel value: {0}'.format(value))
                
        self.write('chan {0}'.format(value))
        self.active_channel_store = value
        
    @property
    @Synchronized()
    def virt_both_persistent_switch_heaters(self):
        """
        The heaters on both channels. Control over both is desirable in order to avoid eddy currents in the system.
        """

        heaters = [channel.persistent_switch_heater for channel in self.channels[1:]]
        all_heaters_same = all(heaters[0] == heater for heater in heaters)
            
        # Output based on states.
        if all_heaters_same == True:
            return heaters[0]
        else:
            return 'unequal'
    
    @virt_both_persistent_switch_heaters.setter
    @Synchronized()
    def virt_both_persistent_switch_heaters(self,value):
        if value not in self.allowed_both_heaters:
            raise ValueError('Invalid heater switch value: {0}'.format(value))
        
        #can set value on or off and it will write to all channels
        for channel in self.channels[1:]:
            channel.persistent_switch_heater = value
            
    @property
    @Synchronized()
    def virt_both_units(self):
        """
        Get current units of both device's channels.
        """
        both_units = [channel.units for channel in self.channels[1:]]
        all_units_same = all(both_units[0] == units for units in both_units)

        # Output based on states.
        if all_units_same == True:
            return both_units[0]
        else:
            return 'unequal'
            
    
    @virt_both_units.setter
    def virt_both_units(self,value):
        """
        Set current units on both channels.
        """
        if value not in self.allowed_both_units:
            raise ValueError('Invalid units: {0}'.format(value))
        
        #write to all channels
        for channel in self.channels[1:]:
            channel.units = value
            
            
name = 'Model 4G'
implementation = Model4G
