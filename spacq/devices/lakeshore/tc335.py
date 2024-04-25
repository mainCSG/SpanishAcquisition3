import logging
log = logging.getLogger(__name__)

from spacq.interface.resources import Resource
from spacq.tool.box import Synchronized

from ..abstract_device import AbstractDevice
from ..tools import quantity_wrapped, quantity_unwrapped

"""
Lakeshore 335 Temperature Controller

Reads temperature
Reads powerA #,powerB
write setPoint
"""

class TC335(AbstractDevice):
    """
    Interface for Lakeshore 335 Temperature Controller
    """

    allowed_ranges = set(['Off','Low','Medium','High'])
    
    def _setup(self):
        AbstractDevice._setup(self)

        # Resources.
        self.read_only = ['temperature', 'powerA']#, 'powerB']
        for name in self.read_only:
            self.resources[name] = Resource(self, name)

        self.read_write = ['setPointA', 'rangeA'] #'setPointB', 'rangeB'
        for name in self.read_write:
            self.resources[name] = Resource(self, name, name)

        self.resources['temperature'].units = 'K'
        self.resources['powerA'].converter = float
        self.resources['setPointA'].units = 'K'
        self.resources['rangeA'].allowed_values = self.allowed_ranges
        #self.resources['powerB'].converter = float
        #self.resources['setPointB'].units = 'K'
        #self.resources['rangeB'].allowed_values = self.allowed_ranges

        # Make dict relating power settings to commands sent
        self.power_range = {'Off':'0','Low':'1','Medium':'2','High':'3'}
                                
    @Synchronized()
    def _connected(self):
        AbstractDevice._connected(self)


    @Synchronized()
    def reset(self):
        """
        Reset the device to its default state.
        """

        log.info('Resetting "{0}".'.format(self.name))
        self.write('*rst')


    @property
    @quantity_wrapped('K')
    @Synchronized()
    def temperature(self):
        """
        The value measured by the device, as a quantity in K.
        """

        self.status.append('Taking reading')

        try:
            log.debug('Getting temperature reading.')
            status = int(self.ask('rdgst?'))
            if status == 0:
                result = float(self.ask('krdg?'))
            elif status <= 17:
                result = -1 #This corresponds to T.UNDER
            else:
                result = -2 # This should correspond to S.OVER, or other errors

            log.debug('Got reading: {0}'.format(result))

            return result
        finally:
            self.status.pop()

    @property
    @Synchronized()
    def powerA(self):
        """
        The value measured by the device, as a quantity in %.
        """
        return float(self.ask('HTR? 1'))
    
    #@property
    #@Synchronized()
    #def powerB(self):
    #	"""
    #	The value measured by the device, as a quantity in %.
    #	"""

    #	return float(self.ask('HTR? 2'))    
    
    @property
    @quantity_wrapped('K')
    def setPointA(self):
        return float(self.ask('SETP? 1'))
        
    @setPointA.setter
    @quantity_unwrapped('K')
    def setPointA(self, value):
        self.write('SETP 1,{0}'.format(value))
        self.currentSetPointA = value
    
    #@property
    #@quantity_wrapped('K')
    #def setPointB(self):
    #	return self.currentSetPointB
        
    #@setPointB.setter
    #@quantity_unwrapped('K')
    #def setPointB(self, value):
    #	self.write('SETP 2,{0}'.format(value))
    #	self.currentSetPointB = value

    @property
    def rangeA(self):
        value = int(self.ask('RANGE? 1'))
        reverse_dict = {0:'Off',1:'Low',2:'Medium',3:'High'}
        return reverse_dict[value]
        
    @rangeA.setter
    def rangeA(self, value):
            #if value not in self.allowed_ranges:
        #	raise ValueError('Invalid rangeA value: {0}'.format(value))
    
        self.write('RANGE 1,{0}'.format(self.power_range[value]))
        self.currentRangeA = value

    #@property
    #def rangeB(self):
    #	return self.currentRangeB
        
    #@rangeB.setter
    #def rangeB(self, value):
            #if value not in self.allowed_ranges:
        #	raise ValueError('Invalid rangeB value: {0}'.format(value))
    
    #	self.write('RANGE 2,{0}'.format(value))
    #	self.currentRangeB = value	
    

name = '335 Temperature Controller'
implementation = TC335
