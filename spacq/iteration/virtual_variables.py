import logging
log = logging.getLogger(__name__)

import numpy
from itertools import groupby
import operator
from spacq.gui.tool.box import MessageDialog
from functools import partial, wraps

# TODO: consider need for constant variable type in virtual?
# TODO: fix message dialog

# This is needed so don't get recursion depth errors. Decorators
def update_current_f(f):
    @wraps(f)
    def wrapped(self):
        self.current_f = f.__name__

        log.debug('Entering function: {0}'.format(self.current_f))

        return f(self)

    return wrapped


# currently in config/variables.py like linspaceConfig
class virtLinSpaceConfig(object):
    """
    Like LinSpaceConfig but with order...
    """
    def __init__(self, name='var', initial=0.0, final=0.0, steps=1, order=1):
        self.name = name
        self.initial = initial
        self.final = final
        self.steps = steps
        self._order = order

        self.close_callback= None

    @property
    def steps(self):
        return self._steps

    @property
    def order(self):
        return self._order

    @steps.setter
    def steps(self, value):
        if value <= 0:
            raise ValueError('Number of steps must be positive, not "{0}".'.format(value))

        self._steps = value

    def __iter__(self):
        return iter(numpy.linspace(self.initial, self.final, self.steps))

    def __len__(self):
        return self.steps

class DependentConfig(object):
    """
    Like LinSpaceConfig but with order...
    """
    def __init__(self, name='var', expression='1'):
        self.name = name
        self.expression = expression


    def DependentFunctionMath(self, virt_headings, virt_values):

        editExpression = self.expression

        for i,heading in enumerate(virt_headings):
            # shouldnt be issue because disabled are always on tail?
            editExpression = editExpression.replace(heading,'virt_values[:,{0}]'.format(i))

        # if nothing gets entered for a enabled variable
        if editExpression is None or editExpression == '':
            result = numpy.zeros((1,len(virt_values)))[0]
        else:
            try:
                # Allows for constant input
                result = numpy.ones((1,len(virt_values)))[0]*float(editExpression)
            except ValueError as e:
                try:
                    result = eval(editExpression)
                except NameError as e:
                    # MessageDialog(self,  str(e), 'Could not evaluate').Show()
                    print('Could not evaluate.')

        tempEval = eval(editExpression)

        return result

# something like SweepController:
class virtSweepController(object):
    def __init__(self, variables, num_items):

        # Sorted by order at this point
        self.variables = variables
        self.num_items = num_items

        self.names = []

        # Number of variables
        self.var_count = 0
        for order in self.variables:
            self.var_count += len(order)
            for var in order:
                self.names.append(var.name)

        # for writing to csv
        self.value_history = numpy.zeros([self.num_items,self.var_count])

        # Count for iterations of needed outputs
        self.item = -1

        # definitely needed
        self.orders = [vars[0].order for vars in self.variables]
        self.orders.reverse()


    def compute_order_periods(self):
        """
        This function computes the number of elements iterated before each order changes.
        """
        periods = []
        orders = []

        for group in reversed(self.variables):
            #skip if vars in group are consts.
            # no such const, or maybe we should?
            # if group[0].use_const != 1:
            num_in_group = None

            #get the length of the group
            for var in group:
                num_in_var = len(var)

                if num_in_group is None or num_in_var < num_in_group:
                    num_in_group = num_in_var

            #append the period of this group and its order.
            if not periods:
                periods.append(num_in_group)
            else:
                periods.append(periods[-1]*num_in_group)

            orders.append(group[0].order)

        #  no conditions
        # create a dict.
        self.order_periods = dict(list(zip(orders, periods)))

    def create_iterator(self, pos):
        """
        Create an iterator for an order of variables.
        """
        return zip(*(iter(var) for var in self.variables[pos]))

    # maybe some renaming
    def sweepTable(self):

        """
        Initialize values and possibly devices.
        """

        self.iterators = None
        self.current_values = None
        self.last_values = None

        self.compute_order_periods()

        # TODO: fill in
        while self.item < self.num_items - 1:

            """
            Get the next set of values from the iterators.
            """

            self.item += 1
            if self.current_values is not None:
                self.last_values = self.current_values[:]

            if self.iterators is None:
                # First time around.
                self.iterators = []
                for pos in range(len(self.variables)):
                    self.iterators.append(self.create_iterator(pos))

                self.current_values = [next(it) for it in self.iterators]
                self.changed_indices = list(range(len(self.variables)))
                # create an other copy that we will not change
                self.full_indices = list(range(len(self.variables)))

                # Calculate where the end of each order is.
            else:
                pos = len(self.variables) - 1
                while pos >= 0:
                    try:
                        # Gets new values here
                        self.current_values[pos] = next(self.iterators[pos])
                        break
                    except StopIteration:
                        self.iterators[pos] = self.create_iterator(pos)
                        self.current_values[pos] = next(self.iterators[pos])

                        pos -= 1

                self.changed_indices = list(range(pos, len(self.variables)))


            """
            Write the next values to the table
            """

            # fills in value_history
            counter = 0
            for pos in self.full_indices[0:]:
                for i, (var,value) in enumerate(zip(self.variables[pos],self.current_values[pos])):
                    self.value_history[self.item][counter] = value
                    counter += 1



# copeid from iteration/variables.py
def sort_output_variables(variables):
    """
    Sort and group the variables based on their order.

    The returned values are:
        variables sorted and grouped by their order
        number of items in the Cartesian product of the orders
    """

    # Ignore disabled variables entirely!
    # no enabled used right now
    # variables = [var for var in variables if var.enabled]

    if not variables:
        return [], 0

    order_attr = operator.attrgetter('order')
    ordered = sorted((var for var in variables), key=order_attr, reverse=True)
    grouped = [tuple(vars) for order, vars in groupby(ordered, order_attr)]

    num_items = 1
    for group in grouped:
        num_in_group = None

        for var in group:
            num_in_var = len(var)

            if num_in_group is None or num_in_var < num_in_group:
                num_in_group = num_in_var

        num_items *= num_in_group

    return grouped, num_items
