from itertools import groupby, islice
import numpy
import operator

from spacq.interface.units import Quantity


def sort_output_variables(variables):
	"""
	Sort and group the variables based on their order.

	The returned values are:
		variables sorted and grouped by their order
		number of items in the Cartesian product of the orders
	"""

	# Ignore disabled variables entirely!
	variables = [var for var in variables if var.enabled]

	if not variables:
		return [], 0

	const_vars = tuple([var for var in variables if var.use_const])

	order_attr = operator.attrgetter('order')
	ordered = sorted((var for var in variables if not var.use_const), key=order_attr, reverse=True)
	grouped = [tuple(vars) for order, vars in groupby(ordered, order_attr)]

	num_items = 1
	for group in grouped:
		num_in_group = None

		for var in group:
			num_in_var = len(var)

			if num_in_group is None or num_in_var < num_in_group:
				num_in_group = num_in_var

		num_items *= num_in_group
		
	if const_vars:
		grouped.insert(0, const_vars)

	return grouped, num_items

def sort_condition_variables(variables):
	"""
	Sort and group condition variables based on their order.
	This function is similar to sort_output_variables.

	The returned value is:
		variables sorted and grouped by their order

	"""

	# Ignore disabled variables entirely!
	variables = [var for var in variables if var.enabled]

	if not variables:
		return []

	order_attr = operator.attrgetter('order')
	ordered = sorted(variables, key=order_attr, reverse=True)
	grouped = [tuple(vars) for order, vars in groupby(ordered, order_attr)]

	return grouped

class Variable(object):
	"""
	An abstract superclass for all variables.
	"""

	def __init__(self, name, enabled=False):
		self.name = name
		self.enabled = enabled


class ConditionVariable(Variable):
	"""
	A condition variable. Used to define conditions to make loops in the sweep controller indefinite.
	"""
	
	def __init__(self, order, resource_names=None, conditions=[], wait = '100 ms', *args, **kwargs):
		Variable.__init__(self, *args,**kwargs)
		
		self.order = order
		self.conditions = conditions
		self._wait = Quantity(wait)
		self.resource_names = resource_names
		
	def evaluate_conditions(self, condition_resources=None):
		"""
		Checks the conditions where condition_resources contains the resources required to evaluate the
		conditions.
		"""
		# We take OR of all the conditions.
		boolean = False
		for condition in self.conditions:
			boolean = boolean or condition.evaluate(condition_resources)
		
		if not self.conditions:
			boolean = True
		
		return boolean
	
	@property
	def wait(self):
		return str(self._wait)

	@wait.setter
	def wait(self, value):
		wait = Quantity(value)
		wait.assert_dimensions('s')
				
		self._wait = wait
		
	def __str__(self):
		return '['+', '.join(map(str,self.conditions))+']'
		
class Condition(object):
	"""
	A class used to represent a condition.
	"""
	
	allowed_types = set(['string', 'float', 'integer', 'quantity', 'resource name','resource'])
	
	def __init__(self, type1, type2, arg1, op_symbol, arg2):
		for type in [type1, type2]:
			if type not in self.allowed_types:
				raise ValueError('Condition cannot be of type {0}.'.format(type))
		
		self.type1 = type1
		self.type2 = type2
		self.arg1 = arg1
		self.arg2 = arg2
		self.op_symbol = op_symbol
				
	def evaluate(self, resources=None):
		"""
		Evaluate a condition. 'resources' comes as a list of 2-tuples (name, resource obj).
		"""
		op = {'>':operator.gt, '==':operator.eq, '!=':operator.ne, '<':operator.lt}
		
		arg1_to_evaluate = self.arg1
		arg2_to_evaluate = self.arg2
		
		# We retrieve the values from the resources if the arguments are resource names
		if resources:
			for name, resource in resources:
				# Note that the ordering of the 'and' statements here makes use of python's shortcircuiting.
				# Upon reversing boolean arguments, there could be a case that throws an exception if a string
				# is being compared against a quantity.  This is because of the overloading of __eq__ for Quantity.
				if self.type1 == 'resource name' and name == self.arg1:
					arg1_to_evaluate = resource.value
				if self.type2 == 'resource name' and name == self.arg2:
					arg2_to_evaluate = resource.value
					
		if self.type1 == 'resource':
			arg1_to_evaluate = self.arg1.value
		if self.type2 == 'resource':
			arg2_to_evaluate = self.arg2.value

		boolean = op[self.op_symbol](arg1_to_evaluate, arg2_to_evaluate)
		
		return boolean



	def __str__(self):
		return '{0} {1} {2}'.format(self.arg1,self.op_symbol,self.arg2)
		
		


class InputVariable(Variable):
	"""
	An input (measurement) variable.
	"""
	def __init__(self, resource_name='', *args, **kwargs):
		Variable.__init__(self, *args, **kwargs)
		
		self.resource_name = resource_name


class OutputVariable(Variable):
	"""
	An abstract superclass for output variables.
	"""

	# Maximum number of initial values to display in string form.
	display_values = 4

	# Maximum number of values to search through for the end.
	search_values = 1000

	def __init__(self, order, config=None, wait='100 ms', const=0.0, use_const=False, resource_name='', *args, **kwargs):
		Variable.__init__(self, *args, **kwargs)
		
		self.resource_name = resource_name

		self.order = order

		if config is not None:
			self.config = config
		else:
			self.config = LinSpaceConfig(0.0, 0.0, 1)

		# Iteration parameters.
		self._wait = Quantity(wait)
		self.const = const
		self.use_const = use_const

		# Smooth set.
		self.smooth_steps = 100
		self.smooth_from = False
		self.smooth_to = False
		self.smooth_transition = False

		self.type = 'float'
		self.units = None

	@property
	def wait(self):
		return str(self._wait)

	@wait.setter
	def wait(self, value):
		wait = Quantity(value)
		wait.assert_dimensions('s')
				
		self._wait = wait


	def with_type(self, value):
		"""
		Set to the correct type, and wrap with the correct units.
		"""

		if self.type == 'integer':
			return int(value)
		elif self.type == 'float':
			return value
		elif self.type == 'quantity' and self.units is not None:
			return Quantity(value, self.units)
		else:
			raise ValueError('Invalid variable setup; type: {0}, units: {1}'.format(self.type, self.units))

	@property
	def raw_iter(self):
		if self.use_const:
			return [self.const]
		else:
			return iter(self.config)

	def __iter__(self):
		return (self.with_type(x) for x in self.raw_iter)

	def __len__(self):
		if self.use_const:
			return 1
		else:
			return len(self.config)

	def __str__(self):
		found_values = islice(self.raw_iter, 0, self.search_values + 1)

		if self.type == 'integer':
			found_values = [int(x) for x in found_values]
		else:
			found_values = list(found_values)

		shown_values = ', '.join('{0:g}'.format(x) for x in found_values[:self.display_values])

		if len(found_values) > self.display_values:
			if len(found_values) > self.display_values + 1:
				shown_values += ', ...'

			if len(found_values) <= self.search_values:
				shown_values += ', {0:g}'.format(found_values[-1])

		smooth_from = '(' if not self.use_const and self.smooth_from else '['
		smooth_to = ')' if not self.use_const and self.smooth_to else ']'
		units = ' {0}'.format(self.units) if self.units is not None else ''
		return '{0}{1}{2}{3}'.format(smooth_from, shown_values, smooth_to, units)


class LinSpaceConfig(object):
	"""
	Linear space variable configuration.
	"""

	def __init__(self, initial=0.0, final=0.0, steps=1):
		self.initial = initial
		self.final = final
		self.steps = steps

	@property
	def steps(self):
		return self._steps

	@steps.setter
	def steps(self, value):
		if value <= 0:
			raise ValueError('Number of steps must be positive, not "{0}".'.format(value))

		self._steps = value

	def __iter__(self):
		return iter(numpy.linspace(self.initial, self.final, self.steps))

	def __len__(self):
		return self.steps


class ArbitraryConfig(object):
	"""
	Variable configuration for arbitrary values.
	"""

	def __init__(self, values):
		self.values = values

	def __iter__(self):
		return iter(self.values)

	def __len__(self):
		return len(self.values)
