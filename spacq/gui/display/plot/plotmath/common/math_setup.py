import wx

from .....tool.box import Dialog

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
		
class MathSetupDialog_Derivative(Dialog):
	"""
	Math configuration dialog (for derivative).
	"""

	def __init__(self, parent, headings, axis_names, *args, **kwargs):
		Dialog.__init__(self, parent, *args, **kwargs)

		self.axes = [None for _ in axis_names]
		
		self.step_size = 1

		# Dialog.
		dialog_box = wx.BoxSizer(wx.VERTICAL)

		## Axis setup.
		axis_panel = AxisSelectionPanel(self, axis_names, headings, self.OnAxisSelection)
		dialog_box.Add(axis_panel)

		# Derivative Slider
		slider_box = wx.BoxSizer(wx.HORIZONTAL)
		dialog_box.Add(slider_box, flag=wx.CENTER)

		self.slider_title = wx.StaticText(self, label='Step Size:')
		slider_box.Add(self.slider_title)

		self.reading = wx.StaticText(self, label='01')
		slider_box.Add(self.reading)

		self.step_slider = wx.Slider(self, value=1, minValue=1, maxValue= 20, size=(200,-1), style=wx.SL_HORIZONTAL)
		self.Bind(wx.EVT_SCROLL, self.OnSliderScroll, self.step_slider)
		slider_box.Add(self.step_slider)

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

	def OnSliderScroll(self, evt=None):
		self.step_size = self.step_slider.GetValue()

		self.reading.SetLabel(str(self.step_size))

	def OnOk(self, evt=None):
		title, d_data = self.calculate()
		self.dheading = title
		self.ddata = d_data
		self.Destroy()

class MathSetupDialog_Function(Dialog):
	"""
	Math configuration dialog(for functions).
	"""

	def __init__(self, parent, headings, axis_names, *args, **kwargs):
		Dialog.__init__(self, parent, *args, **kwargs)

		self.axes = [None for _ in axis_names]
		
		# Dialog.
		dialog_box = wx.BoxSizer(wx.VERTICAL)

		## Axis setup.
		axis_panel = AxisSelectionPanel(self, axis_names, headings, self.OnAxisSelection)
		dialog_box.Add(axis_panel)

		## Inputs.
		input_sizer = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
		input_sizer.AddGrowableCol(1, 1)
		dialog_box.Add(input_sizer, proportion=1, flag=wx.EXPAND|wx.ALL, border=5)

		input_sizer.Add(wx.StaticText(self, label='Scalar function of '+', '.join(axis_names)+':'),
				flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.function_input = wx.TextCtrl(self)
		self.function_input.SetMinSize((300, -1))
		input_sizer.Add(self.function_input, flag=wx.EXPAND)

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
		title, d_data = self.calculate()
		self.dheading = title
		self.ddata = d_data
		self.Destroy()
