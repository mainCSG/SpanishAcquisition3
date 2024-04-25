from ....tool.box import MessageDialog
from .common.math_setup import MathSetupDialog_Derivative
from numpy import concatenate

class DerivativeMathSetupDialog(MathSetupDialog_Derivative):

	dheading = []
	ddata = []
	
	def __init__(self, parent, headings, data, *args, **kwargs):
		MathSetupDialog_Derivative.__init__(self, parent, headings, ['d', '/d'], *args, **kwargs)

		self.parent = parent
		self.headings = headings
		self.data = data


		def calculate(self):
			try:
					y_data, x_data = [self.data[:,axis].astype(float) for axis in self.axes]
			except ValueError as e:
					MessageDialog(self, str(e), 'Invalid value').Show()
					return
	
		y_label, x_label = [self.headings[x] for x in self.axes]
		title = 'd{0}/d{1}'.format(y_label, x_label)
		
		derivative_loop = len(x_data)

		if x_data[0] == x_data[1]:
			for i,x in enumerate(x_data[1:]):
				if x != x_data[0]:
					derivative_loop = i+1
					break
			h = x_data[derivative_loop]-x_data[0]
			d_data = [ [-9999] ]*len(y_data)
			y_small = [ -9999 ] * (len(y_data)/derivative_loop)
			for k in range(0,derivative_loop):
				for j in range(0,len(y_data)/derivative_loop):
					y_small[j] = y_data[j*derivative_loop+k]
				if self.step_size >= len(y_small)/2:
					self.step_size = 1
				for i,y in enumerate(y_small):
					if i - self.step_size < 0:
						d_data[i*derivative_loop+k] = [ (y_small[i+self.step_size]-y_small[0])/((i+self.step_size)*h) ]
					elif len(y_small) - i - self.step_size < 1:
						d_data[i*derivative_loop+k] = [ (y_small[len(y_small)-1]-y_small[i-self.step_size])/((len(y_small)-1-i+self.step_size)*h) ]
					else:
						d_data[i*derivative_loop+k] = [ (y_small[i+self.step_size]-y_small[i-self.step_size])/(2*self.step_size*h) ]


		else:		
			for i,x in enumerate(x_data[1:]):
				if x == x_data[0]:
					derivative_loop = i+1
					break
			
			h = x_data[1]-x_data[0]
			d_data = [ [-9999] ]*len(y_data)
			for j in range(0,len(y_data)/derivative_loop):
				y_small = y_data[derivative_loop*j:(j+1)*derivative_loop]
				if self.step_size >= len(y_small)/2:
					self.step_size = 1
				for i,y in enumerate(y_small):
							if i - self.step_size < 0:
								d_data[i+j*derivative_loop] = [ (y_small[i+self.step_size]-y_small[0])/((i+self.step_size)*h) ]
							elif len(y_small) - i - self.step_size < 1:
								d_data[i+j*derivative_loop] = [ (y_small[len(y_small)-1]-y_small[i-self.step_size])/((len(y_small)-1-i+self.step_size)*h) ]
							else:
								d_data[i+j*derivative_loop] = [ (y_small[i+self.step_size]-y_small[i-self.step_size])/(2*self.step_size*h) ]

		return(title,d_data)


