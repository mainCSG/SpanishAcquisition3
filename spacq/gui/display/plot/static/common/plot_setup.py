import wx

from .....tool.box import Dialog, MessageDialog
from spacq.tool.box import Enum

"""
Plot configuration.
"""

class AxisSelectionPanel(wx.Panel):
	"""
	A panel for choosing the headings to be used for the axes.
	"""

	def __init__(self, parent, axes, headings, selection_callback, *args, **kwargs):
		wx.Panel.__init__(self, parent, *args, **kwargs)

		self.selection_callback = selection_callback

		# Panel.
		panel_box = wx.BoxSizer(wx.HORIZONTAL)

		## Axes.
		self.axis_lists = []

		for axis in axes:
			axis_static_box = wx.StaticBox(self, label=axis)
			axis_box = wx.StaticBoxSizer(axis_static_box, wx.VERTICAL)
			panel_box.Add(axis_box, proportion=1, flag=wx.EXPAND|wx.ALL, border=5)

			axis_list = wx.ListBox(self, choices=headings)
			axis_list.SetMinSize((-1, 300))
			self.Bind(wx.EVT_LISTBOX, self.OnAxisSelection, axis_list)
			axis_box.Add(axis_list, proportion=1, flag=wx.EXPAND)

			self.axis_lists.append(axis_list)

		self.SetSizer(panel_box)

	def OnAxisSelection(self, evt=None):
		"""
		Announce the latest selection.
		"""

		result = [None if list.Selection == wx.NOT_FOUND else list.Selection for
				list in self.axis_lists]

		self.selection_callback(result)


class PlotSetupDialog(Dialog):

	bounds_format = '{0:.4e}'
	"""
	Plot configuration dialog.
	"""

	def __init__(self, parent, headings, axis_names, max_mesh = [-1, -1], interp_mode = '_remove', *args, **kwargs):
		Dialog.__init__(self, parent, *args, **kwargs)

		self.max_mesh = max_mesh #derivative classes can choose to call this constructor with or wihtout the max_mesh argument;
					 #defaults to [-1, -1] meaning 'skip'
		self.interp_mode = interp_mode  #derivative classes can call this constructor with or without the interp_mode argument;
						#defualt is -1 meaning 'skip' -- show no radio buttons and do no interpolation (for 2D plots)
		self.axes = [None for _ in axis_names]

		# Dialog.
		dialog_box = wx.BoxSizer(wx.VERTICAL)

		## Axis setup.
		axis_panel = AxisSelectionPanel(self, axis_names, headings, self.OnAxisSelection)
		dialog_box.Add(axis_panel)

		## Input: Interpolation Mode: Radio Buttons
		InterpolationModes = Enum(['_none','_x','_y','_2d_no_mask', '_2d_full_mask'])
		self.InterpolationModes = InterpolationModes
		if (not interp_mode == '_remove'):
			try:
				if not any( interp_mode == x for x in InterpolationModes ):
					raise ValueError(interp_mode)
			except ValueError as e:
				MessageDialog(self, 'Bad interpolation mode '+str(e)+'. No interplolation assumed.', 'ValueError').Show()
				self.interp_mode = '_remove'

		if (not self.interp_mode == '_remove'):
			radio_box = wx.BoxSizer(wx.HORIZONTAL)
			radio_static_box = wx.StaticBox(self, label='Interpolation Mode:')
			radio_settings_box = wx.StaticBoxSizer(radio_static_box, wx.HORIZONTAL)
			radio_box.Add(radio_settings_box, proportion=1, flag=wx.EXPAND|wx.ALL, border=5)
			dialog_box.Add(radio_box, flag=wx.CENTER)

			self.rb1 = wx.RadioButton(self, -1, 'None\n(Not Implemented Yet)', (10, 10), style=wx.RB_GROUP)
			self.rb2 = wx.RadioButton(self, -1, 'x-axis only\n(Not Implemented Yet)', (10, 10))
			self.rb3 = wx.RadioButton(self, -1, 'y-axis only\n(SLOW!)', (10, 10))
			self.rb4 = wx.RadioButton(self, -1, '2D (no mask)', (10, 10))
			self.rb5 = wx.RadioButton(self, -1, '2D with mask\n(warning: very high memory usage)', (10, 10))

			radio_settings_box.Add(self.rb1, flag=wx.RIGHT, border=10)
			radio_settings_box.Add(self.rb2, flag=wx.RIGHT, border=10)
			radio_settings_box.Add(self.rb3, flag=wx.RIGHT, border=10)
			radio_settings_box.Add(self.rb4, flag=wx.RIGHT, border=10)
			radio_settings_box.Add(self.rb5, flag=wx.RIGHT, border=10)
		
			#Boy I miss C-style swith-case	
			if self.interp_mode == InterpolationModes._none:
				self.rb1.SetValue(True)
			elif self.interp_mode == InterpolationModes._x:
				self.rb2.SetValue(True)
			elif self.interp_mode == InterpolationModes._y:
				self.rb3.SetValue(True)
			elif self.interp_mode == InterpolationModes._2d_no_mask:
				self.rb4.SetValue(True)
			else: 
				self.rb5.SetValue(True)
		## Input: Max Grid Points
		if (all (item > 0 for item in max_mesh)):
			self.has_max_mesh_value = True

			grid_box = wx.BoxSizer(wx.HORIZONTAL)
			button_static_box = wx.StaticBox(self, label='Max Grid Points')
			settings_box = wx.StaticBoxSizer(button_static_box, wx.HORIZONTAL)
			grid_box.Add(settings_box, proportion=1, flag=wx.EXPAND|wx.ALL, border=5)

			dialog_box.Add(grid_box, flag=wx.CENTER)

			### Max X mesh size.
			settings_box.Add(wx.StaticText(self, label='x: '),
				flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
			self.mesh_x_value = wx.TextCtrl(self,
				value=str(max_mesh[0]),
				size=(100, -1), style=wx.TE_PROCESS_ENTER)
			self.Bind(wx.EVT_TEXT_ENTER, self.OnXValue, self.mesh_x_value)
			settings_box.Add(self.mesh_x_value, flag=wx.RIGHT, border=20)

			### Max Y mesh size.
			settings_box.Add(wx.StaticText(self, label='y: '),
				flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
			self.mesh_y_value = wx.TextCtrl(self,
				value=str(max_mesh[1]),
				size=(100, -1), style=wx.TE_PROCESS_ENTER)
			self.Bind(wx.EVT_TEXT_ENTER, self.OnYValue, self.mesh_y_value)
			settings_box.Add(self.mesh_y_value, flag=wx.RIGHT, border=20)
		else:
			self.has_max_mesh_value = False			

		## End buttons.
		button_box = wx.BoxSizer(wx.HORIZONTAL)
		dialog_box.Add(button_box, flag=wx.CENTER)

		self.ok_button = wx.Button(self, wx.ID_OK)
		self.ok_button.Disable()
		self.Bind(wx.EVT_BUTTON, self.OnOk, self.ok_button)
		button_box.Add(self.ok_button)

		cancel_button = wx.Button(self, wx.ID_CANCEL)
		button_box.Add(cancel_button)

		self.SetSizerAndFit(dialog_box)

	def OnAxisSelection(self, values):
		self.axes = values

		self.ok_button.Enable(all(axis is not None for axis in self.axes))

	def OnOk(self, evt=None):
		if not self.interp_mode == '_remove':
			if self.rb1.GetValue():
				self.interp_mode = self.InterpolationModes._none
			if self.rb2.GetValue():
				self.interp_mode = self.InterpolationModes._x
			if self.rb3.GetValue():
				self.interp_mode = self.InterpolationModes._y
			if self.rb4.GetValue():
				self.interp_mode = self.InterpolationModes._2d_no_mask
			if self.rb5.GetValue():
				self.interp_mode = self.InterpolationModes._2d_full_mask

		if self.has_max_mesh_value: # update the values typed in (but ENTER not pressed) for max_x, max_y
			self.OnXValue()
			self.OnYValue()
		if self.make_plot():
			self.Destroy()

			return True

	def OnXValue(self, evt=None):
		value = self.mesh_x_value.Value
		try:
			value = int(value)
		except ValueError:
			value = self.max_mesh[0]

		if (value > 0):
			self.max_mesh[0] = value

		# Update the text box.
		self.mesh_x_value.Value = str(self.max_mesh[0])

	def OnYValue(self, evt=None):
		value = self.mesh_y_value.Value
		try:
			value = int(value)
		except ValueError:
			value = self.max_mesh[1]

		if (value > 0):
			self.max_mesh[1] = value

		# Update the text box.
		self.mesh_y_value.Value = str(self.max_mesh[1])
