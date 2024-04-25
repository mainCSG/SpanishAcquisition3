.. _variable_config:

######################
Variable configuration
######################

Variable configuration panel
****************************

The variable configuration panel is used to set up :ref:`output variables <general_concepts_output_variables>` and :ref:`condition variables <general_concepts_condition_variables>` for an application.

.. _variable_config_figure:

.. figure:: variable_config_list.*
   :alt: Variable configuration.

   ..

   1. The "enabled" checkbox. Variables which do not have this checked (such as **gate 3**) effectively do not exist; this is useful for temporarily disabling variables.
   2. A unique label to identify the variable. This name appears, for example, as a column heading when capturing data.
   3. The order number of variables is used to group them during the sweep. **gate 1** and **gate 4** have the same order, so would be stepped together in the inner loop; **magnetic field** has a higher order number, and so will be stepped alone in the outer loop. **gate 1 condition** would be checked at the end of the inner loop's stepping (ie, before the outer loop changes).
   4. The resource label for the resource to which to write the values. All the resources provided must be writable. If a resource is not provided (such as with **gate 4**), the variable is still stepped in the usual fashion, but its values are discarded. Notice that for conditions, "N/A" is written.  The user is not able to write to this field.
   5. The values over which the output variable will be stepped. If there are too many values, some are omitted from the display. The symbols on either side of the values specify whether that side is set smoothly: "(" and ")" if smoothly (as for **gate 1**); "[" and "]" if not (as for the other variables).

      If there are any units associated with a variable, they are displayed after the values.

      If it is a condition variable, then the conditions will be displayed.

   6. For each step of an output variable, after writing the value to the resource, there is a delay of at least the wait time. In each order, the delay for all output variables is the longest of the wait times in that order. The effective wait time for **gate 4** is 200 ms.

      For condition variables, this represents a delay that is held after a condition is checked and before measurements are taken again.  The condition variable's overall boolean value could change within this timespan.
   7. The "const" checkbox. Variables which have this checked (such as **gate 2**) are considered *constant* and are subject to special consideration in some scenarios.

      Condition variables do not have this attribute.
   8. The const value of a variable is that which it is assumed to take on at rest. The value does nothing on its own, but is used in conjunction with other settings and actions.

      The units associated with a variable apply to the const value as well.

      Condition variables do not have this attribute.
   9. Clicking "Add Output" creates a blank output variable. Similarly, clicking "Add Condition" creates a blank condition variable. Clicking "Remove" permanently removes all selected variables.
   10. The variable settings can be saved to and loaded from the disk. All the configured variables (both enabled and not) are saved at the same time, and existing variables are overwritten by any loaded variables.

To select a variable, click on its row. To select multiple variables, hold down the "ctrl" key while clicking. When several variables are selected, some actions (such as clicking "Remove" or pressing the space bar) act on all of them.

.. tip::
   The user interface is organized so that **gate 2** and **gate 3** are still displayed alongside the other variables with order number 1. However, **gate 2** is set to const, and so will be in a separate virtual order, and **gate 3** is disabled, so will not participate at all.

Variable sweep example
======================

The configuration shown :ref:`above <variable_config_figure>` would result in the following actions during a sweep:

#. Resource **v1** is smoothly stepped from -2.5 V to -5 V.
#. The values are set (with each being written to the appropriate resource, if any):

   ==============  ==============  ========  =======  =======
   Constant order     Order 2      Order 1
   --------------  --------------  --------  -------  -------
       gate 2      magnetic field   gate 1   gate 3   gate 4
   ==============  ==============  ========  =======  =======
   5.6 V           0.001 T         -5.0 V    ---      -5.0 V
   \               \               -4.375 V  \        -3.75 V
   \               \               -3.75 V   \        -2.5 V
   **...**         **...**         **...**   **...**  **...**
   \               \               -0.625 V  \        3.75 V
   \               \               0.0 V     \        5.0 V
   \               0.002 T         -5.0 V    \        -5.0 V
   \               \               -4.375 V  \        -3.75 V
   \               \               -3.75 V   \        -2.5 V
   **...**         **...**         **...**   **...**  **...**
   \               \               -0.625 V  \        3.75 V
   \               \               0.0 V     \        5.0 V
   \               0.005 T         -5.0 V    \        -5.0 V
   \               \               -4.375 V  \        -3.75 V
   \               \               -3.75 V   \        -2.5 V
   \               \               -3.125 V  \        -1.25 V
   \               \               -2.5 V    \        0.0 V
   \               \               -1.875 V  \        1.25 V
   \               \               -1.25 V   \        2.5 V
   \               \               -0.625 V  \        3.75 V
   \               \               0.0 V     \        5.0 V
   ==============  ==============  ========  =======  =======

   Between steps of variables in order 2, if **gate 1** set to smoothly transition, resource **v1** is smoothly stepped from 0.0 V to -5.0 V.
   Also, before each step in order 2 occurs, **gate 1 condition** is evaluated for its current boolean value.  Everytime, it should evaluate to true since **gate 1** always has a value of 0.0 V at the end of order 1.

#. Resource **v1** is smoothly stepped from 0 V to -2.5 V.

Output variable editor dialog
*****************************

The variable editor dialog is used to configure the values over which a variable is stepped. It is opened by double-clicking in the "Values" column of the variable.

.. figure:: variable_config_editor.*
   :alt: Variable editor.

   ..

   1. The value configuration is performed by using one of the available configuration panels.
   2. :ref:`Smooth setting <general_concepts_output_variables_smooth>` configuration.
   3. :ref:`Type and units <general_concepts_output_variables_type>` configuration.

Configuration panels
====================

Linear
------

A linear space is described between the initial and final bounds (inclusive), consisting of the specified number of values. For example, if initial, final, and steps are were to 1, 5, and 9, respectively, the resulting values would be: 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5.

Arbitrary
---------

Values are provided directly as a sequence of comma-separated numbers (with ignored whitespace). For example, the input "1, 32 , -5,6.543,0,0 , 1" would result in the values: 1, 32, -5, 6.543, 0, 0, 1.

From File
---------

Values are provided from a column of comma-separated values (CSV) file. Clicking “Load CSV” opens dialog to select a CSV file from the directory. Heading names of columns of the CSV table are displayed which can be then be selected and preview first three values. Values from selected column of the CSV are auto-filled as an arbitrary input. 

.. _variable_config_condition_variable_editor_dialog:

Condition variable editor dialog
********************************

The condition editor dialog is used to setup the conditions housed within a condition variable.  It is opened by double-clicking the "Values" column of the condition variable.


.. figure:: variable_config_condition_variable_editor.*
   :alt: Condition variable editor.

   ..

1. Conditions are listed here.  Double-clicking on a condition will open the :ref:`condition editor <variable_config_condition_variable_editor_dialog_condition_editor>`.
2. Conditions can be added or removed.


.. _variable_config_condition_variable_editor_dialog_condition_editor:

Condition editor
================

The condition editor is accessed by double-clicking a condition in the :ref:`condition variable editor <variable_config_condition_variable_editor_dialog>`.

.. figure:: variable_config_condition_editor.*
   :alt: Condition editor.

   ..

The operator, the arguments and their types are what define a condition as has been described :ref:`here <general_concepts_condition_variables_conditions>`.
