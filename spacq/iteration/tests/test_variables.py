from nose.tools import assert_raises, eq_
from unittest import main, TestCase

from spacq.interface.units import IncompatibleDimensions, Quantity
from spacq.interface.resources import Resource
from functools import partial

from .. import variables

class SortOutputVariablesTest(TestCase):
	def testEmpty(self):
		"""
		Use no variables.
		"""

		sorted_variables, num_items = variables.sort_output_variables([])

		eq_(sorted_variables, [])
		eq_(num_items, 0)

	def testSingle(self):
		"""
		Use a single variable.
		"""

		var = variables.OutputVariable(config=variables.LinSpaceConfig(-5.0, 5.0, 11),
				name='Name', order=0, enabled=True, const=60.0)

		sorted_variables, num_items = variables.sort_output_variables([var])

		eq_(sorted_variables, [(var,)])
		eq_(num_items, 11)

	def testMultiple(self):
		"""
		Use many variables.
		"""

		vars = [
			variables.OutputVariable(config=variables.LinSpaceConfig(1.0, 5.0, 3),
					name='A', order=3, enabled=True),
			variables.OutputVariable(config=variables.LinSpaceConfig(11.0, 12.0, 2),
					name='B', order=2, enabled=True, const=10.0),
			variables.OutputVariable(config=variables.LinSpaceConfig(-99.0, 0.0),
					name='D', order=1, enabled=True, const=9.0, use_const=True),
			variables.OutputVariable(config=variables.LinSpaceConfig(21.0, 25.0, 20),
					name='C', order=2, enabled=True),
			variables.OutputVariable(config=variables.LinSpaceConfig(0.0, 0.0, 1),
					name='E', order=4),
			variables.OutputVariable(
					name='F', order=5, enabled=True, const=5.5, use_const=True),
		]

		sorted_variables, num_items = variables.sort_output_variables(vars)

		eq_(sorted_variables, [(vars[2], vars[5]), (vars[0],), (vars[1], vars[3])])
		eq_(num_items, 6)

class ConditionVariableTest(TestCase):
	
	# It goes without saying that if condition variables are upgraded
	# with a general boolean parser that these tests will have to be changed.
	
	def testEvaluateConditions(self):
		"""
		See if a condition variable evaluates its conditions
		properly.
		"""
		
		# Define conditions.
		c1 = variables.Condition('integer','integer',1,'<',3) #True
		c2 = variables.Condition('integer','integer',1,'>',3) #False
		
		# Define condition variables.
		cv0 = variables.ConditionVariable(1,conditions=[c1], name='cv0')
		cv1 = variables.ConditionVariable(1,conditions=[c1,c1], name='cv1')
		cv2 = variables.ConditionVariable(1,conditions=[c1,c2], name='cv2')
		cv3 = variables.ConditionVariable(1,conditions=[c2,c2,c2,c1], name='cv3')
		cv4 = variables.ConditionVariable(1,conditions=[c2,c2], name='cv4')
		
		# Evaluate a simple case.
		eq_(cv0.evaluate_conditions(),True)
		
		# Check if it is ORing properly.
		eq_(cv1.evaluate_conditions(),True)
		eq_(cv2.evaluate_conditions(),True)
		eq_(cv3.evaluate_conditions(),True)
		eq_(cv4.evaluate_conditions(),False)
	
	def testEvaluateCondition(self):
		"""
		Test if evaluating conditions works properly
		for different combinations of types.
		"""
		# Some variables to use for tests.
		
		res_bufs = [[], [], [], []]

		def setter(i, value):
			res_bufs[i].append(value)
			
		def getter(i):
			return res_bufs[i][0]
			
			
		a = Quantity('5 T')
		b = Quantity('50 kG')
		c = 'on'

		res0 = Resource(getter=partial(getter,0), setter=partial(setter, 0))
		res0.units = 'T'
		res1 = Resource(getter=partial(getter,1), setter=partial(setter, 1))
		res1.units = 'kG'
		res2 = Resource(getter=partial(getter,2), setter=partial(setter, 2))
		res2.allowed_values = ['on','off']
		
		res0.value = a
		res1.value = b
		res2.value = c

		# Check 2 quantities of equivalent units.
		c1 = variables.Condition('quantity','quantity',a,'==',b)
		eq_(c1.evaluate(), True)
		
		# Check a resource against a quantity.
		c2 = variables.Condition('resource','quantity',res0,'==',a)
		eq_(c2.evaluate(), True)
		
		# Check a resource with a resource.
		c3 = variables.Condition('resource','resource',res0,'==',res1)
		eq_(c3.evaluate(), True)
		
		# Check a resource that has an allowed value with a string.
		c4 = variables.Condition('resource','string',res2,'==',c)
		eq_(c4.evaluate(), True)
		
		# Test evaluating resource names.
		resources = [('res0',res0),('res1',res1),('res2',res2)]
		c3 = variables.Condition('resource name','resource name','res0','==','res1')
		eq_(c3.evaluate(resources), True)
		
		# Check some things that should mess up.
		
		## string instead of quantity.
		try:
			c5 = variables.Condition('resource','string',res0,'==','5 T')
			eq_(c5.evaluate(), True)
		except TypeError:
			pass
		else:
			assert False, 'Expected TypeError.'
		
		## not matching units.
		try:
			c6 = variables.Condition('quantity','quantity',Quantity('5 A'),'==',Quantity('5 T'))
			eq_(c6.evaluate(), True)
		except IncompatibleDimensions:
			pass
		else:
			assert False, 'Expected IncompatibleDimensions error.'
		
		
class OutputVariableTest(TestCase):
	def testAdjust(self):
		"""
		Try to adjust the values after initialization.
		"""

		var = variables.OutputVariable(name='Name', order=1)

		var.config = variables.LinSpaceConfig()

		var.config.steps = 1000
		eq_(var.config.steps, 1000)

		try:
			var.config.steps = -1
		except ValueError:
			pass
		else:
			assert False, 'Expected ValueError.'

		var.wait = '1e2 ms'
		eq_(var.wait, '100 ms')

		try:
			var.wait = '100 Hz'
		except IncompatibleDimensions:
			pass
		else:
			assert False, 'Expected IncompatibleDimensions.'

	def testStr(self):
		"""
		Ensure the variable looks right.
		"""

		var = variables.OutputVariable(name='Name', order=1)

		# Very short.
		var.config = variables.LinSpaceConfig(0.0, 5.0, 3)
		var.type = 'integer'
		eq_(str(var), '[0, 2, 5]')

		# Borderline.
		var.config = variables.LinSpaceConfig(1.0, 5.0, 5)
		var.type = 'float'
		eq_(str(var), '[1, 2, 3, 4, 5]')

		# Short enough.
		var.config = variables.LinSpaceConfig(-200.0, 200.0, 401)
		eq_(str(var), '[-200, -199, -198, -197, ..., 200]')

		# Far too long.
		var.config = variables.LinSpaceConfig(0.0, 100000.0, 100001)
		eq_(str(var), '[0, 1, 2, 3, ...]')

		# Smooth from constant.
		var.smooth_from = True
		eq_(str(var), '(0, 1, 2, 3, ...]')

		# And to.
		var.smooth_to = True
		eq_(str(var), '(0, 1, 2, 3, ...)')

	def testUnits(self):
		"""
		Ensure that values are wrapped with units.
		"""

		var = variables.OutputVariable(name='Name', order=1)
		var.type = 'quantity'
		var.units = 'g.m.s-1'
		var.config = variables.LinSpaceConfig(0.0, -5.0, 3)

		eq_(list(var), [Quantity(x, 'g.m.s-1') for x in [0, -2.5, -5]])
		eq_(str(var), '[0, -2.5, -5] g.m.s-1')

		# Bad combination.
		var.units = None
		assert_raises(ValueError, list, var)


class LinSpaceConfigTest(TestCase):
	def testIterator(self):
		"""
		Create an iterator from a linear space variable.
		"""

		var = variables.OutputVariable(config=variables.LinSpaceConfig(-1.0, -3.0, 5),
				name='Name', order=1, enabled=True, const=10.0)

		# Non-const.
		eq_(len(var), 5)

		it1 = iter(var)
		eq_(list(it1), [-1.0, -1.5, -2.0, -2.5, -3.0])

		# Const.
		var.use_const = True

		eq_(len(var), 1)

		it2 = iter(var)
		eq_(list(it2), [10.0])


class ArbitraryConfigTest(TestCase):
	def testIterator(self):
		"""
		Create an iterator from an arbitrary variable.
		"""

		values = [8, -5, 6.6, 3, 0, 0]

		var = variables.OutputVariable(config=variables.ArbitraryConfig(values),
				name='Name', order=1, enabled=True)

		eq_(len(var), len(values))

		it = iter(var)
		eq_(list(it), values)


if __name__ == '__main__':
	main()
