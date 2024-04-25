from functools import partial
from pubsub import pub
from threading import Lock
from threading import Thread
import wx

from spacq.gui.tool.box import Dialog, OK_BACKGROUND_COLOR, MessageDialog
from spacq.interface.units import Quantity, IncompatibleDimensions
from spacq.interface.resources import AcquisitionThread

"""
Magnet control front panel.

Dev notes:	-Temporary design.  Magnet control is planned to be integrated with
			the resource automation functionality of this program.
			-spacq.devices.iqc.gui.voltage_source.py was used as a guide
			in creating this.
			-the live aspects of this gui are derived from gui.display.plot.live.scalar.py
"""

class Model4GChannelPanel(wx.Panel):
	
	def __init__(self, parent, global_store, subdevice, *args, **kwargs):
		wx.Panel.__init__(self, parent, *args, **kwargs)

		self.global_store = global_store
		self.delay = Quantity(1.0, 's')
		
		# This lock blocks the acquisition thread from acquiring.
		self.running_lock = Lock()
		self.channel_subdevice = subdevice
		
		self.displays = {}
		self.control_state_displays = {}
		self.readout_displays = {}
		self.control_state_list = ['persistent_switch_heater','virt_sync_currents']
		self.readout_list = [	'magnet_current','power_supply_current',
								'persistent_switch_heater', 'high_limit','low_limit','sweep',
								'rate_0','rate_1','rate_2','rate_3','rate_4', 'virt_sync_currents']
		self.measurement_resources = []
		for name in self.readout_list:
			self.displays[name] = []
			self.measurement_resources.append((name, self.channel_subdevice.resources[name]))
		# A list to save acquired data to before outputting to GUI.
		self.measurements = [None] * len(self.measurement_resources)

		# Main Box.
		
		main_box = wx.BoxSizer(wx.VERTICAL)
		
		# Channel Header Box.
		
		channel_header_box = wx.BoxSizer(wx.HORIZONTAL)
		main_box.Add(channel_header_box, flag=wx.EXPAND)
		
		self.channel_button = wx.ToggleButton(self, label='Channel {0} Toggle'.format(self.channel_subdevice.channel))
		self.Bind(wx.EVT_TOGGLEBUTTON, self.OnChannelToggle, self.channel_button)
		self.channel_button.SetValue(False)
		channel_header_box.Add(self.channel_button)
		
		## Control states.
		
		control_state_grid = wx.FlexGridSizer(rows=2, cols=2, vgap=5, hgap=5)
		channel_header_box.Add((0, 0), 1, wx.EXPAND)
		channel_header_box.Add(control_state_grid, flag=wx.ALIGN_RIGHT, border = 20)
		
		for control_state_name in self.control_state_list:
			control_state_display = wx.TextCtrl(self, size=(100, -1), style=wx.TE_READONLY)
			control_state_display.BackgroundColour = wx.LIGHT_GREY
			control_state_grid.Add(control_state_display, flag=wx.ALIGN_RIGHT)
			self.displays[control_state_name].append(control_state_display)
			self.control_state_displays[control_state_name] = control_state_display
		
		# reverse our dictionary for key retrieval by item.
		self.inv_control_state_displays = dict((v,k) for k, v in self.control_state_displays.items())

		# Readouts.
		
		readout_static_box = wx.StaticBox(self, label = 'Readouts')
		readout_box = wx.StaticBoxSizer(readout_static_box, wx.VERTICAL)
		main_box.Add(readout_box, flag=wx.EXPAND, proportion=1)
		
#		readout_grid = wx.FlexGridSizer(rows=len(self.readout_list), cols=2, vgap=5, hgap=5)
		readout_grid = wx.FlexGridSizer(rows=len(self.readout_list), cols=3, vgap=5, hgap=5) #TODO: for debugging model4g GUI...replace when no longer needed.
		readout_box.Add(readout_grid, flag=wx.ALIGN_RIGHT)
		
		self.checkboxes = {}
				
		## Setup individual labels + displays
		
		for resource_name in self.readout_list:
			
			### Checkbox. #TODO: for debugging model4g GUI...remove when no longer needed.
			checkbox = wx.CheckBox(self)
			readout_grid.Add(checkbox, flag = wx.ALIGN_LEFT)
			self.checkboxes[resource_name] = checkbox
			
			### Label.
			label = resource_name.replace('_',' ').title()
			readout_grid.Add(wx.StaticText(self, label=label + ':'),
					flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
			
			### Display.
			display = wx.TextCtrl(self, size=(100, -1), style=wx.TE_READONLY)
			display.BackgroundColour = wx.LIGHT_GREY
			self.displays[resource_name].append(display)
			self.readout_displays[resource_name] = display
									
			### Connect display to GUI.
			readout_grid.Add(self.displays[resource_name][-1], flag=wx.ALIGN_RIGHT)
			
		# reverse our dictionary for key retrieval by item.
		self.inv_readout_displays = dict((v,k) for k, v in self.readout_displays.items())
		
		# Controls.
		
		self.control_static_box = wx.StaticBox(self, label='Controls')
		self.control_box=wx.StaticBoxSizer(self.control_static_box, wx.VERTICAL)
		main_box.Add(self.control_box, flag=wx.EXPAND)
		
		## Persistent Heater Switch.
		
		heater_box = wx.BoxSizer(wx.HORIZONTAL)
		self.control_box.Add(heater_box, flag=wx.ALIGN_RIGHT)
		
		heater_box.Add(wx.StaticText(self, label='Persistent Switch Heater:'),
				flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		
		self.heater_toggle = wx.ToggleButton(self, label='on/off', size=(100,-1))
		initial_state = self.channel_subdevice.persistent_switch_heater
		self.heater_toggle.SetValue(True if initial_state == 1 else 0)
		self.Bind(wx.EVT_TOGGLEBUTTON, self.OnHeaterToggle, self.heater_toggle)
		heater_box.Add(self.heater_toggle,flag=wx.ALIGN_RIGHT)
		
		## Sweeper Control Box.
		
		sweeper_static_box = wx.StaticBox(self, label = 'Sweep')
		sweeper_box = wx.StaticBoxSizer(sweeper_static_box, wx.VERTICAL)
		self.control_box.Add(sweeper_box, flag=wx.EXPAND)
		
		sweep_buttons_box = wx.BoxSizer(wx.HORIZONTAL)
		sweeper_box.Add(sweep_buttons_box, flag = wx.CENTER|wx.ALL)
		
		### Sweep buttons.
		
		sweep_buttons_grid = wx.FlexGridSizer(rows=2, cols=2, vgap=5, hgap=5)
		sweep_buttons_box.Add(sweep_buttons_grid, flag=wx.CENTER|wx.ALL)
		
		sweepup_button = wx.Button(self, label='up')
		sweepzero_button = wx.Button(self, label='zero')
		sweepdown_button = wx.Button(self, label='down')
		sweeppause_button = wx.Button(self, label='pause')
		self.Bind(wx.EVT_BUTTON, self.OnSweepUp, sweepup_button)
		self.Bind(wx.EVT_BUTTON, self.OnSweepZero, sweepzero_button)
		self.Bind(wx.EVT_BUTTON, self.OnSweepDown, sweepdown_button)
		self.Bind(wx.EVT_BUTTON, self.OnSweepPause, sweeppause_button)
		sweep_buttons_grid.Add(sweepup_button)
		sweep_buttons_grid.Add(sweepzero_button)
		sweep_buttons_grid.Add(sweepdown_button)
		sweep_buttons_grid.Add(sweeppause_button)
		
		### Current syncing.
		
		####some space
		
				
		sync_button = wx.Button(self, label='sync currents')
		self.Bind(wx.EVT_BUTTON, self.OnSyncCurrents, sync_button)
		sweep_buttons_box.Add(sync_button, flag=wx.LEFT|wx.CENTER, border = 20)

		## Limits.
		
		limit_static_box = wx.StaticBox(self, label = 'Limits')
		limit_box = wx.StaticBoxSizer(limit_static_box, wx.VERTICAL)
		self.control_box.Add(limit_box,flag=wx.EXPAND)
						
		limits_grid = wx.FlexGridSizer(rows=2, cols=3, vgap=5, hgap=5)
		limits_grid.AddGrowableCol(1,1)

		limit_box.Add(limits_grid, flag=wx.ALIGN_RIGHT)
		
		### High Limit
		
		limits_grid.Add(wx.StaticText(self, label='High Limit:'),
				flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		
		set_hilim_button = wx.Button(self, label='Set', style=wx.BU_EXACTFIT)
		self.Bind(wx.EVT_BUTTON, self.OnSetHighLimit, set_hilim_button)
		limits_grid.Add(set_hilim_button,flag=wx.ALIGN_RIGHT)
		
		self.hilim_input = wx.TextCtrl(self, size=(100, -1))
		limits_grid.Add(self.hilim_input, flag=wx.EXPAND)
		
		### Low Limit
		
		limits_grid.Add(wx.StaticText(self, label='Low Limit:'),
				flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		
		set_lolim_button = wx.Button(self, label='Set', style=wx.BU_EXACTFIT)
		self.Bind(wx.EVT_BUTTON, self.OnSetLowLimit, set_lolim_button)
		limits_grid.Add(set_lolim_button,flag=wx.ALIGN_RIGHT)
		
		self.lolim_input = wx.TextCtrl(self, size=(100, -1))
		limits_grid.Add(self.lolim_input)
		
		## Rates.
		
		rates_static_box = wx.StaticBox(self, label = 'Rates')
		rates_box = wx.StaticBoxSizer(rates_static_box, wx.VERTICAL)
		self.control_box.Add(rates_box,flag=wx.EXPAND)
		
		## used to have content of rates box all right aligned. 
		rates_inner_box = wx.BoxSizer(wx.HORIZONTAL)
		rates_box.Add(rates_inner_box, flag=wx.ALIGN_RIGHT)
		
		menu_items = []
		for resource in self.readout_list:
			if resource.startswith('rate_'):
				menu_items.append(resource) 
		
		self.rates_menu = wx.ComboBox(self,choices = menu_items, style=wx.CB_READONLY)
		self.rates_menu.SetStringSelection(menu_items[0])
		rates_inner_box.Add(self.rates_menu, flag=wx.ALIGN_RIGHT)
		
		set_rate_button = wx.Button(self, label='Set', style=wx.BU_EXACTFIT)
		self.Bind(wx.EVT_BUTTON, self.OnSetRate, set_rate_button)
		rates_inner_box.Add(set_rate_button,flag=wx.ALIGN_RIGHT)
		
		self.rate_input = wx.TextCtrl(self, size=(100, -1))
		rates_inner_box.Add(self.rate_input, flag=wx.ALIGN_RIGHT)
			
		# Finish GUI building.
		
		self.SetSizerAndFit(main_box)
		
		# Default behaviour.
		
		## start with... 
		### ...the threads locked out of acquisition.
		self.running_lock.acquire()
		### ...controls disabled.
		self.RecursiveEnableSizer(self.control_box,False)
		
		# Threading.
		
		self.acqthreads = []
		#TODO: implement with a normal thread instead, to avoid the use of a dummy call to a resource.
		guicallback = partial(wx.CallAfter, self.Update)
		self.guiupdatethread = AcquisitionThread(self.delay, guicallback, resource=self.channel_subdevice.resources['persistent_switch_heater'], running_lock=self.running_lock)
		self.acqthreads.append(self.guiupdatethread)
		self.guiupdatethread.daemon = True
		self.guiupdatethread.start()
		
	def __del__(self):
		try:
			
#			if self.channel_button.GetValue() == False:
#				self.running_lock.release()
			for thread in self.acqthreads:
				thread.resource = None
				thread.done = True
				thread.join()
				del thread
			
#			self.close()
		except Exception:
			pass

	def UpdateReadouts(self, resource_name, value):
		"""
		Update appropriate readouts with a new resource value.
		Also update button permissions.
		"""
		if resource_name in list(self.readout_displays.keys()):
			if self.checkboxes[resource_name].Value == False: #TODO: for debugging model4g GUI...remove when no longer needed.
				return
			
		for display in self.displays[resource_name]:
			
			#perform alterations to output based on where the resource is being readout in GUI.
			
			inv_cont_dict = self.inv_control_state_displays
			if display in list(inv_cont_dict.keys()):
				if inv_cont_dict[display] == 'persistent_switch_heater':
					if value == 'on':
						display.BackgroundColour = OK_BACKGROUND_COLOR
					elif value == 'off':
						display.BackgroundColour = wx.LIGHT_GREY
					
					value_readout = 'heater {0}'.format(value)
					
				elif inv_cont_dict[display] == 'virt_sync_currents':
					if value == 'synced':
						display.BackgroundColour = OK_BACKGROUND_COLOR
					elif value == 'not synced':
						display.BackgroundColour = wx.LIGHT_GREY
					#display as-is
					value_readout = value
			elif display in list(self.inv_readout_displays.keys()):
				#display as-is
				value_readout = value
			
			display.SetValue(str(value_readout))
			
			# User Permissions
			
			# if currents don't match, heater toggle should be disabled.
			if display in list(inv_cont_dict.keys()):
				if inv_cont_dict[display] == 'virt_sync_currents':
					if value == 'synced':
						self.heater_toggle.Enable()
					else:
						self.heater_toggle.Disable()
			
			
	def Update(self, dummyval):
		"""
		Acquire data and then update the GUI with this data.
		
		Note: code taken from sweep controller.
		"""

		#this loop sets up separate threads for each resource.
		thrs = []
		for i, (name, resource) in enumerate(self.measurement_resources):
			if resource is not None:
				def save_callback(value, i=i):
					self.measurements[i] = value

				callback = partial(wx.CallAfter, partial(self.read_resource, name, resource, save_callback))
				thr = Thread(target=callback)
				thrs.append(thr)
				thr.daemon = True
				thr.start()

		for thr in thrs:
			thr.join()

		#this code saves the values to the GUI readouts.
		for i, (name,_) in enumerate(self.measurement_resources):
			self.UpdateReadouts(name, self.measurements[i])
		
			
	def read_resource(self, name, resource, save_callback):
		"""
		Read a value from a resource and handle exceptions.
		
		Note: code taken from sweep controller.
		"""
		
		if name in list(self.readout_displays.keys()):
			if self.checkboxes[name].Value == False: #TODO: for debugging model4g GUI...remove when no longer needed.
				return

		try:
			value = resource.value
		except Exception as e:
			if self.resource_exception_handler is not None:
				self.resource_exception_handler(name, e, write=False)
			return

		save_callback(value)

	def OnChannelToggle(self, evt=None):
		toggle = self.channel_button.GetValue()
		if toggle == True:
			self.running_lock.release()
		elif toggle == False:
			self.running_lock.acquire()
			
		self.RecursiveEnableSizer(self.control_box, toggle)
		
		#permission defaults.
		self.heater_toggle.Disable()
		
		
	def OnSweepDown(self, evt=None):
		self.channel_subdevice.resources['sweep'].value = 'down'
		
	def OnSweepUp(self, evt=None):
		self.channel_subdevice.resources['sweep'].value = 'up'
		
	def OnSweepZero(self, evt=None):
		self.channel_subdevice.resources['sweep'].value = 'zero'
		
	def OnSweepPause(self, evt=None):
		self.channel_subdevice.resources['sweep'].value = 'pause'
		
	def OnSetRate(self, evt=None):
		try:
			Quantity(self.rate_input.GetValue())
		except ValueError as e:
			MessageDialog(self, str(e), 'Invalid value').Show()
			return False
		
		range_id = self.rates_menu.GetCurrentSelection()
		resource = self.channel_subdevice.resources['rate_{0}'.format(range_id)]
		new_value = self.rate_input.GetValue()
		try:
			resource.value = resource.convert(new_value)
		except IncompatibleDimensions:
			MessageDialog(self, ValueError('Expected dimensions to match "{0}"'.format(resource.units))).Show()
		
	def OnHeaterToggle(self, evt=None):
		if self.heater_toggle.GetValue() == True:
			new_value = 'on'
		if self.heater_toggle.GetValue() == False:
			new_value = 'off'
		self.channel_subdevice.resources['persistent_switch_heater'].value = new_value
		
	def OnSetHighLimit(self, evt=None):
		try:
			Quantity(self.hilim_input.GetValue())
		except ValueError as e:
			MessageDialog(self, str(e), 'Invalid value').Show()
			return False
		
		new_value = self.hilim_input.GetValue()
		resource = self.channel_subdevice.resources['high_limit']
		try:
			resource.value = resource.convert(new_value)
		except IncompatibleDimensions:
			MessageDialog(self, str(ValueError('Expected dimensions to match "{0}"'.format(resource.units)))).Show()
		
	def OnSetLowLimit(self, evt=None):
		try:
			Quantity(self.lolim_input.GetValue())
		except ValueError as e:
			MessageDialog(self, str(e), 'Invalid value').Show()
			return False
		
		new_value = self.lolim_input.GetValue()
		resource = self.channel_subdevice.resources['low_limit']
		try:
			resource.value = resource.convert(new_value)
		except IncompatibleDimensions:
			MessageDialog(self, ValueError('Expected dimensions to match "{0}"'.format(resource.units))).Show()
		
		
	def OnSyncCurrents(self, evt=None):
		self.channel_subdevice.resources['virt_sync_currents'].value = 'start'
		
	def close(self):
		"""
		Perform cleanup.
		"""		
		# Ensure the threads exits.
		if self.channel_button.GetValue() == False:
			self.running_lock.release()
		for thread in self.acqthreads:
			thread.resource = None
			thread.done = True
			thread.join()
			del thread
			
	def RecursiveEnableSizer(self,wx_sizer, toggle):
		'''
		Helper function that accesses all subwindows of a wxPython 
		sizer, and enables or disables them based on toggle.
		'''
		children = wx_sizer.GetChildren()
		for item in children:
			
			window = item.GetWindow()
			sizer = item.GetSizer()
			
			if sizer:
				#recurse
				self.RecursiveEnableSizer(sizer,toggle)
			elif window:
				window.Enable(toggle)


class Model4GFrontPanel(wx.Panel):
	"""
	GUI for controlling the magnet.
	"""
	
	def __init__(self, parent, global_store, model4g, *args, **kwargs):
		wx.Panel.__init__(self, parent, *args, **kwargs)

		self.global_store = global_store
		self.model4g = model4g
		self.running = False
		

		# Main Panel.
		panel_box = wx.BoxSizer(wx.VERTICAL)
				
		## Channels box.
		channels_box = wx.BoxSizer(wx.HORIZONTAL)
		panel_box.Add(channels_box)
		
		### Channel boxes.
		self.channel_panels = []
		for channel_subdevice in self.model4g.channels:
			if channel_subdevice is not None:
								
				channel_static_box = wx.StaticBox(self)
				channel_box_sizer = wx.StaticBoxSizer(channel_static_box, wx.VERTICAL)
								
				#### Channel Inputs/Outputs.
				channel_panel = Model4GChannelPanel(self, global_store, channel_subdevice)
				channel_box_sizer.Add(channel_panel)
				channels_box.Add(channel_box_sizer)
				
				self.channel_panels.append(channel_panel)

		
		
		self.SetSizerAndFit(panel_box)
				
	def close(self):
		#TODO: wxPython would probably have a nicer way of sending a close down through children.
		for channel_panel in self.channel_panels:
			channel_panel.close()
		
class Model4GFrontPanelDialog(Dialog):
	"""
	A wrapper for Model4GFrontPanel.
	"""

	def __init__(self, parent, global_store, model4g_name, *args, **kwargs):
		# If the device doesn't exist, give up.
		try:
			model4g = global_store.devices[model4g_name].device
		except (KeyError, AttributeError):
			self.Destroy()

			return

		Dialog.__init__(self, parent, title='Model4G Front Panel', *args, **kwargs)

		self.model4g_name = model4g_name

		# Dialog.
		dialog_box = wx.BoxSizer(wx.VERTICAL)

		## Settings panel.
		self.panel = Model4GFrontPanel(self, global_store, model4g)
		dialog_box.Add(self.panel)

		self.SetSizerAndFit(dialog_box)
		
		self.Bind(wx.EVT_CLOSE, self.OnClose)

		# Subscriptions.
		pub.subscribe(self.msg_device, 'device.added')
		pub.subscribe(self.msg_device, 'device.removed')
	
	def msg_device(self, name, value=None):
		if name == self.model4g_name:
			# Device has changed, so we can't trust it anymore.
			self.Destroy()

			return
		
	def OnClose(self, evt):
		self.panel.close()
		evt.Skip()