import logging
log = logging.getLogger(__name__)

import functools
import numpy
from pubsub import pub
from threading import Lock
from time import localtime
import wx
from wx.lib.agw import floatspin

from spacq.interface.resources import AcquisitionThread
from spacq.interface.units import Quantity

from ....config.measurement import MeasurementConfigPanel
from ....tool.box import Dialog, MessageDialog

try:
	from ..two_dimensional import TwoDimensionalPlot
except ImportError as e:
	plot_available = False
	log.debug('Could not import TwoDimensionalPlot: {0}'.format(str(e)))
else:
	plot_available = True

"""
A historical live view plot for list values.
"""


class PlotSettings(object):
	"""
	Wrapper for all the settings configured via dialog.
	"""

	def __init__(self):
		self.enabled = plot_available
		self.update_x = True
		self.update_y = True
		self.delay = Quantity(0.2, 's')


class PlotSettingsDialog(Dialog):
	"""
	Set up the live view plot.
	"""

	def __init__(self, parent, ok_callback, *args, **kwargs):
		Dialog.__init__(self, parent=parent, title='Plot settings')

		self.ok_callback = ok_callback

		dialog_box = wx.BoxSizer(wx.VERTICAL)

		# Enabled.
		self.enabled_checkbox = wx.CheckBox(self, label='Enabled')
		if not plot_available:
			self.enabled_checkbox.Disable()
		dialog_box.Add(self.enabled_checkbox, flag=wx.ALL, border=5)

		# Capture.
		capture_static_box = wx.StaticBox(self, label='Capture')
		capture_box = wx.StaticBoxSizer(capture_static_box, wx.VERTICAL)
		capture_sizer = wx.FlexGridSizer(rows=2, cols=2, vgap=5, hgap=5)
		capture_box.Add(capture_sizer, flag=wx.CENTER)
		dialog_box.Add(capture_box, flag=wx.EXPAND|wx.ALL, border=5)

		## Delay.
		capture_sizer.Add(wx.StaticText(self, label='Delay (s):'),
				flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.delay_input = floatspin.FloatSpin(self, min_val=0.2, max_val=1e4, increment=0.1, digits=2)
		capture_sizer.Add(self.delay_input, flag=wx.CENTER)

		# End buttons.
		button_box = wx.BoxSizer(wx.HORIZONTAL)
		dialog_box.Add(button_box, flag=wx.CENTER)

		ok_button = wx.Button(self, wx.ID_OK)
		self.Bind(wx.EVT_BUTTON, self.OnOk, ok_button)
		button_box.Add(ok_button)

		cancel_button = wx.Button(self, wx.ID_CANCEL)
		button_box.Add(cancel_button)

		self.SetSizerAndFit(dialog_box)

	def OnOk(self, evt=None):
		self.ok_callback(self)

		self.Destroy()

	def GetValue(self):
		plot_settings = PlotSettings()
		plot_settings.enabled = self.enabled_checkbox.Value
		plot_settings.delay = Quantity(self.delay_input.GetValue(), 's')

		return plot_settings

	def SetValue(self, plot_settings):
		self.enabled_checkbox.Value = plot_settings.enabled
		self.delay_input.SetValue(plot_settings.delay.value)


class ListLiveViewPanel(wx.Panel):
	"""
	A panel to display a live view plot of a list resource.
	"""

	def __init__(self, parent, global_store, *args, **kwargs):
		wx.Panel.__init__(self, parent, *args, **kwargs)

		self.global_store = global_store
		self._measurement_resource_name = None

		# Defaults.
		self.plot_settings = PlotSettings()
		self.unit_conversion = 0

		self.enabled = True
		self.capturing_data = False
		self.restart_live_view = False
		self.resource_backup = None

		# csv save file information
		self.save_path = ''
		self.defaultName=''

		# Initialize recorded values.
		self.init_values()

		# This lock blocks the acquisition thread from acquiring.
		self.running_lock = Lock()

		# Plot and toolbar.
		display_box = wx.BoxSizer(wx.VERTICAL)

		## Plot.
		if plot_available:
			self.plot = TwoDimensionalPlot(self, color='blue')
			display_box.Add(self.plot.control, proportion=1, flag=wx.EXPAND)

#			self.plot.x_label = 'Waveform time (s)'
#			self.plot.y_label = 'History'
		else:
			display_box.Add((500, -1), proportion=1, flag=wx.EXPAND)

		## Controls.
		if plot_available:
			controls_box = wx.BoxSizer(wx.HORIZONTAL)
			display_box.Add(controls_box, flag=wx.CENTER|wx.ALL, border=5)

			### Manual data export
			saveData_static_box = wx.StaticBox(self, label='Last trace')
			saveData_box = wx.StaticBoxSizer(saveData_static_box, wx.HORIZONTAL)
			controls_box.Add(saveData_box, flag=wx.CENTER)

			self.csv_button = wx.Button(self, label='Save to .csv')
			self.Bind(wx.EVT_BUTTON, self.onSave, self.csv_button)
			saveData_box.Add(self.csv_button, flag=wx.CENTER)

			### Capture.
			capture_static_box = wx.StaticBox(self, label='Control')
			capture_box = wx.StaticBoxSizer(capture_static_box)
			controls_box.Add(capture_box, flag=wx.CENTER)

			self.run_button = wx.Button(self, label='Run')
			self.Bind(wx.EVT_BUTTON, self.OnRun, self.run_button)
			capture_box.Add(self.run_button, flag=wx.CENTER)

			self.pause_button = wx.Button(self, label='Pause')
			self.Bind(wx.EVT_BUTTON, self.OnPause, self.pause_button)
			capture_box.Add(self.pause_button, flag=wx.CENTER)

			self.reset_button = wx.Button(self, label='Reset')
			self.Bind(wx.EVT_BUTTON, self.OnReset, self.reset_button)
			capture_box.Add(self.reset_button, flag=wx.CENTER)

			### Settings.
			settings_static_box = wx.StaticBox(self, label='Settings')
			settings_box = wx.StaticBoxSizer(settings_static_box, wx.HORIZONTAL)
			controls_box.Add(settings_box, flag=wx.CENTER|wx.LEFT, border=10)

			self.plot_settings_button = wx.Button(self, label='Plot...')
			self.Bind(wx.EVT_BUTTON, self.OnPlotSettings, self.plot_settings_button)
			settings_box.Add(self.plot_settings_button, flag=wx.CENTER)

		self.SetSizer(display_box)

		# Acquisition thread.
		callback = functools.partial(wx.CallAfter, self.add_values)
		self.acq_thread = AcquisitionThread(self.plot_settings.delay, callback,
				running_lock=self.running_lock)
		self.acq_thread.daemon = True
		self.acq_thread.start()

		# Wait for a resource to begin capturing.
		self.OnPause()
		self.run_button.Disable()

		# Subscriptions.
		pub.subscribe(self.msg_resource, 'resource.added')
		pub.subscribe(self.msg_resource, 'resource.removed')
		pub.subscribe(self.msg_data_capture_start, 'data_capture.start')
		pub.subscribe(self.msg_data_capture_data, 'data_capture.data')
		pub.subscribe(self.msg_data_capture_stop, 'data_capture.stop')

	@property
	def running(self):
		return self.pause_button.Enabled

	@property
	def resource(self):
		return self.acq_thread.resource

	@resource.setter
	def resource(self, value):
		# Ignore unreadable resources.
		if value is not None and not value.readable:
			value = None

		if self.running:
			# Currently running.
			running = True
			self.OnPause()
		else:
			running = False

		self.acq_thread.resource = value

		self.run_button.Enable(value is not None)

		# Resume if applicable.
		if running:
			self.OnRun()

	@property
	def measurement_resource_name(self):
		if self._measurement_resource_name is None:
			return ''
		else:
			return self._measurement_resource_name

	@measurement_resource_name.setter
	def measurement_resource_name(self, value):
		if value:
			self._measurement_resource_name = value
			try:
				self.resource = self.global_store.resources[self._measurement_resource_name]
			except KeyError:
				self.resource = None
		else:
			self._measurement_resource_name = None
			self.resource = None

	def init_values(self):
		"""
		Clear captured values.
		"""

		self._times = numpy.array([])
		self._values = numpy.array([])

	def update_plot(self):
		"""
		Redraw the plot.
		"""

		# Wait for at least one line.
		if not len(self._times) > 0:
			display_time = [0]
			display_values = [0]
		else:
			display_time = self._times
			display_values = self._values

		if self.plot_settings.update_x:
			self.plot.x_autoscale()
		if self.plot_settings.update_y:
			self.plot.y_autoscale()

		self.plot.x_data, self.plot.y_data = display_time, display_values

	def add_values(self, values):
		"""
		Update the plot with a new list of values.
		"""

		if not self.plot_settings.enabled:
			return

		# Extract the times and the data values.
		times, values = list(zip(*values))

		# Update values.
		self._values = numpy.append(numpy.array([]), values)
		self._times = numpy.append(numpy.array([]),times)

		# Plot.
		self.update_plot()

	def close(self):
		"""
		Perform cleanup.
		"""

		# Unsubscriptions.
		pub.unsubscribe(self.msg_resource, 'resource.added')
		pub.unsubscribe(self.msg_resource, 'resource.removed')
		pub.unsubscribe(self.msg_data_capture_start, 'data_capture.start')
		pub.unsubscribe(self.msg_data_capture_data, 'data_capture.data')
		pub.unsubscribe(self.msg_data_capture_stop, 'data_capture.stop')

		# Ensure the thread exits.
		self.acq_thread.resource = None
		self.acq_thread.done = True
		if not self.running:
			self.running_lock.release()
		self.acq_thread.join()
		del self.acq_thread

	def onSave(self, evt=None):
		"""
		save the latest trace to a manually named csv
		"""
		outArray = numpy.column_stack((self._times,self._values))
		
		self.defaultName = 'listTrace_{0:04}-{1:02}-{2:02}_{3:02}-{4:02}-{5:02}.csv'.format(*localtime())
		fdlg = wx.FileDialog(self, "Save last trace", "", self.defaultName, "CSV files(*.csv)|*.*", wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
		if fdlg.ShowModal() == wx.ID_OK:
			self.save_path = fdlg.GetPath()
			if not(self.save_path.endswith(".csv")):
				self.save_path = self.save_path + ".csv"
			numpy.savetxt(self.save_path,outArray,delimiter=',')

	def OnRun(self, evt=None):
		"""
		Let the acquisition thread run.
		"""

		self.run_button.Disable()

		if self.acq_thread.resource is None:
			return

		self.running_lock.release()

		self.pause_button.Enable()

	def OnPause(self, evt=None):
		"""
		Block the acquisition thread.
		"""

		if not self.running:
			return

		self.running_lock.acquire()

		if self.acq_thread.resource is not None:
			self.run_button.Enable()
		self.pause_button.Disable()

	def OnReset(self, evt=None):
		self.init_values()
		self.update_plot()

	def OnPlotSettings(self, evt=None):
		"""
		Open the plot settings dialog.
		"""

		def ok_callback(dlg):
			self.plot_settings = dlg.GetValue()

		dlg = PlotSettingsDialog(self, ok_callback)
		dlg.SetValue(self.plot_settings)
		dlg.Show()

	def msg_resource(self, name, value=None):
		if self.measurement_resource_name is not None and name == self.measurement_resource_name:
			self.resource = value

	def msg_data_capture_start(self, name):
		if name == self.measurement_resource_name:
			if self.enabled:
				self.capturing_data = True

	def msg_data_capture_data(self, name, value):
		if name == self.measurement_resource_name:
			if self.capturing_data:
				self.add_values(value)

	def msg_data_capture_stop(self, name):
		if name == self.measurement_resource_name:
			if self.capturing_data:
				self.capturing_data = False


class ListMeasurementFrame(wx.Frame):
	def __init__(self, parent, global_store, *args, **kwargs):
		wx.Frame.__init__(self, parent, *args, **kwargs)

		# Frame.
		frame_box = wx.BoxSizer(wx.VERTICAL)

		## Measurement setup.
		self.measurement_config_panel = MeasurementConfigPanel(self, global_store, scaling=False)
		frame_box.Add(self.measurement_config_panel, flag=wx.EXPAND)

		## Live view.
		self.live_view_panel = ListLiveViewPanel(self, global_store)
		self.live_view_panel.SetMinSize((-1, 400))
		frame_box.Add(self.live_view_panel, proportion=1, flag=wx.EXPAND)

		self.SetSizerAndFit(frame_box)

		self.Bind(wx.EVT_CLOSE, self.OnClose)

	def OnClose(self, evt):
		if self.live_view_panel.capturing_data:
			msg = 'Cannot close, as a sweep is currently in progress.'
			MessageDialog(self, msg, 'Sweep in progress').Show()

			evt.Veto()
			return

		self.measurement_config_panel.close()
		self.live_view_panel.close()

		evt.Skip()
