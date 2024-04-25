#############
Virtual Setup
#############

The Virtual Setup is an application that allows the user to prepare output variables as functions of linear swept virtual variables. This serves as a utility to for the ‘From File’ option of the ‘Output variable editor dialog’ in Acquisition.

.. figure:: virtual_setup_menu.*
   :alt: Example of virtual variable linear sweep and dependent functions.

In the top panel there is fields to enter the virtual variable name, initial value, final value, steps, and order in the same syntax as the ‘Variable configuration’ portion of the ‘Acquisition’ program. In the bottom panel dependent variables can be setup. They are defined as entered functions of the linear virtual variables. Upon completion, the ‘Evaluation / Write to CSV’ button will generate a CSV file composed of the values of both the virtual variables and the dependent variables following the same variable sweep format of ‘Acquisition’ by the order of the virtual variables. The dependent variables can then be utilized in Acquisition by adding them through the ‘From File’ option and setting them all to the same order number in order to be incremented together.
