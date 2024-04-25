import wx

from ....tool.box import MessageDialog
from .common.math_setup import MathSetupDialog_Function
from numpy import *

class FunctionMathSetupDialog(MathSetupDialog_Function):

	dheading = []
	ddata = []
	
	def __init__(self, parent, headings, data, *args, **kwargs):
		MathSetupDialog_Function.__init__(self, parent, headings, ['X'], *args, **kwargs)

		self.parent = parent
		self.headings = headings
		self.data = data


		def calculate(self):
			try:
				y_data = [self.data[:,x].astype(float) for x in self.axes]
				y_name = [self.headings[x] for x in self.axes]
			except ValueError as e:
				MessageDialog(self, str(e), 'Invalid value').Show()
				return

		title = 'y = {0}'.format(self.function_input.Value.replace('X',y_name[0]))
		y_data = y_data[0]
		d_data = eval(self.function_input.Value.replace('X','y_data'))
		d_data = d_data.reshape(d_data.size,1)
		return(title,d_data)


class FunctionMathSetupDialog2arg(MathSetupDialog_Function):

	dheading = []
	ddata = []
	
	def __init__(self, parent, headings, data, *args, **kwargs):
		MathSetupDialog_Function.__init__(self, parent, headings, ['X','Y'], *args, **kwargs)

		self.parent = parent
		self.headings = headings
		self.data = data


		def calculate(self):
			try:
				f_data = [self.data[:,x].astype(float) for x in self.axes]
				y_name = [self.headings[x] for x in self.axes]
			except ValueError as e:
					MessageDialog(self, str(e), 'Invalid value').Show()
					return

		title = 'z = {0}'.format(self.function_input.Value.replace('X',y_name[0]).replace('Y',y_name[1]))
		x_data = f_data[0]
		y_data = f_data[1]
		d_data = eval(self.function_input.Value.replace('X','x_data').replace('Y','y_data'))
		d_data = d_data.reshape(d_data.size,1)
		return(title,d_data)


