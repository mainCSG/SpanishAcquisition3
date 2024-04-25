import wx

from spacq.tool.box import triples_to_mesh, triples_to_mesh_y

from ....tool.box import MessageDialog
from ..colormapped import ColormappedPlot
from .common.plot_setup import PlotSetupDialog

class ColormappedPlotPanel(wx.Panel):
	def __init__(self, parent, color_data, x_bounds, y_bounds, x_label, y_label,
			*args, **kwargs):
		wx.Panel.__init__(self, parent, *args, **kwargs)

		# Panel.
		panel_box = wx.BoxSizer(wx.VERTICAL)

		## Plot.
		self.plot = ColormappedPlot(self, x_bounds, y_bounds)
		panel_box.Add(self.plot.control, proportion=1, flag=wx.EXPAND)

		self.SetSizer(panel_box)

		self.plot.x_label, self.plot.y_label = x_label, y_label
		self.plot.color_data = color_data


class ColormappedPlotFrame(wx.Frame):
	bounds_format = '{0:.4e}'

	def __init__(self, parent, color_data, x_bounds, y_bounds, x_label, y_label,
			*args, **kwargs):
		wx.Frame.__init__(self, parent, *args, **kwargs)

		# Frame.
		frame_box = wx.BoxSizer(wx.VERTICAL)

		## Plot panel.
		self.panel = ColormappedPlotPanel(self, color_data, x_bounds, y_bounds,
				x_label, y_label)
		self.panel.SetMinSize((400, 300))
		frame_box.Add(self.panel, proportion=1, flag=wx.EXPAND)
		## Settings.
		settings_box = wx.BoxSizer(wx.HORIZONTAL)
		frame_box.Add(settings_box, flag=wx.CENTER)

		### Minimum value.
		settings_box.Add(wx.StaticText(self, label='Min: '),
				flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.minimum_value_input = wx.TextCtrl(self,
				value=self.bounds_format.format(self.panel.plot.low_setting),
				size=(100, -1), style=wx.TE_PROCESS_ENTER)
		self.Bind(wx.EVT_TEXT_ENTER, self.OnMinValue, self.minimum_value_input)
		settings_box.Add(self.minimum_value_input, flag=wx.RIGHT, border=20)

		### Maximum value.
		settings_box.Add(wx.StaticText(self, label='Max: '),
				flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.maximum_value_input = wx.TextCtrl(self,
				value=self.bounds_format.format(self.panel.plot.high_setting),
				size=(100, -1), style=wx.TE_PROCESS_ENTER)
		self.Bind(wx.EVT_TEXT_ENTER, self.OnMaxValue, self.maximum_value_input)
		settings_box.Add(self.maximum_value_input)

		self.SetSizerAndFit(frame_box)

	def OnMinValue(self, evt=None):
		value = self.minimum_value_input.Value
		try:
			value = float(value)
		except ValueError:
			value = 'auto'

		if value <= self.panel.plot.high_setting:
			self.panel.plot.low_setting = value

		# Update the text box.
		self.minimum_value_input.Value = self.bounds_format.format(self.panel.plot.low_setting)

	def OnMaxValue(self, evt=None):
		value = self.maximum_value_input.Value
		try:
			value = float(value)
		except ValueError:
			value = 'auto'

		if value >= self.panel.plot.low_setting:
			self.panel.plot.high_setting = value

		# Update the text box.
		self.maximum_value_input.Value = self.bounds_format.format(self.panel.plot.high_setting)


class ColormappedPlotSetupDialog(PlotSetupDialog):
	def __init__(self, parent, headings, data, *args, **kwargs):
		#Limit the number of grid points on each axis:
		self.max_mesh = [401, 401] #default value passed to parent constructor. Pass [-1,-1] to remove feature from all colorplots
		PlotSetupDialog.__init__(self, parent, headings, ['x', 'y', 'color'], self.max_mesh, '_2d_no_mask',
				*args, **kwargs)

		self.parent = parent
		self.headings = headings
		self.data = data

	def make_plot(self):
		try:
			x_data, y_data, z_data = [self.data[:,axis].astype(float) for axis in self.axes]
		except ValueError as e:
			MessageDialog(self, str(e), 'Invalid value').Show()
			return

		try:
			if self.interp_mode == '_2d_no_mask':
				color_data, x_bounds, y_bounds, _ = triples_to_mesh(x_data, y_data, z_data, self.max_mesh, has_mask=False)
			elif self.interp_mode == '_2d_full_mask':
				color_data, x_bounds, y_bounds, _ = triples_to_mesh(x_data, y_data, z_data, self.max_mesh, has_mask=True)
			elif self.interp_mode == '_y':
				color_data, x_bounds, y_bounds, _ = triples_to_mesh_y(x_data, y_data, z_data, self.max_mesh)
			else:
				MessageDialog(self, 'This feature is not yet impelemted. Sorry!', 'Not immplemented!').Show()
		except Exception as e:
			MessageDialog(self, str(e), 'Conversion failure').Show()
			return

		x_label, y_label, z_label = [self.headings[x] for x in self.axes]
		title = '{0} vs ({1}, {2})'.format(z_label, x_label, y_label)

		frame = ColormappedPlotFrame(self.parent, color_data, x_bounds, y_bounds,
				x_label, y_label, title=title)
		frame.Show()

		return True
