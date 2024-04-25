import wx

from numpy import array
from spacq.interface.units import Quantity
from spacq.iteration.variables import OutputVariable, LinSpaceConfig, ArbitraryConfig
from spacq.iteration.variables import ConditionVariable, Condition

from ..tool.box import Dialog, MessageDialog, load_pickled, save_pickled, load_csv
from spacq.gui.display.table.generic import VirtualListCtrl
import spacq.gui.objectlistview as ObjectListView

"""
An interface for creating and editing Variable objects.
"""


class VariableColumnDefn(ObjectListView.ColumnDefn):
    """
    A column with useful defaults.
    """

    def __init__(self, width=90, align='centre', groupKeyGetter='order', *args, **kwargs):
        ObjectListView.ColumnDefn.__init__(self, width=width, align=align,
                                           groupKeyGetter=groupKeyGetter, *args, **kwargs)

        # No auto-width if space filling.
        if self.isSpaceFilling:
            self.width = 0


class LinSpaceConfigPanel(wx.Panel):
    def __init__(self, parent, *args, **kwargs):
        wx.Panel.__init__(self, parent, *args, **kwargs)

        # Panel.
        panel_box = wx.BoxSizer(wx.VERTICAL)

        # Config.
        config_sizer = wx.FlexGridSizer(rows=3, cols=2,  vgap=5, hgap=5)
        config_sizer.AddGrowableCol(1, 1)
        panel_box.Add(config_sizer, proportion=1, flag=wx.EXPAND)

        # Initial.
        config_sizer.Add(wx.StaticText(self, label='Initial:'),
                         flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.ALL, border=5)
        self.initial_input = wx.TextCtrl(self)
        config_sizer.Add(self.initial_input, flag=wx.EXPAND | wx.ALL, border=5)

        # Final.
        config_sizer.Add(wx.StaticText(self, label='Final:'),
                         flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.ALL, border=5)
        self.final_input = wx.TextCtrl(self)
        config_sizer.Add(self.final_input, flag=wx.EXPAND | wx.ALL, border=5)

        # Steps.
        config_sizer.Add(wx.StaticText(self, label='Steps:'),
                         flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.ALL, border=5)
        self.steps_input = wx.SpinCtrl(self, min=1, initial=1, max=int(1e9))
        config_sizer.Add(self.steps_input, flag=wx.EXPAND | wx.ALL, border=5)

        self.SetSizerAndFit(panel_box)

    def GetValue(self):
        # Ensure the values are sane.
        try:
            initial = float(self.initial_input.Value)
        except ValueError:
            raise ValueError('Invalid initial value.')

        try:
            final = float(self.final_input.Value)
        except ValueError:
            raise ValueError('Invalid final value.')

        return LinSpaceConfig(initial, final, self.steps_input.Value)

    def SetValue(self, config):
        self.initial_input.Value, self.final_input.Value, self.steps_input.Value = (str(config.initial),
                                                                                    str(config.final), config.steps)


class ArbitraryConfigPanel(wx.Panel):
    def __init__(self, parent, *args, **kwargs):
        wx.Panel.__init__(self, parent, *args, **kwargs)

        # Panel.
        panel_box = wx.BoxSizer(wx.VERTICAL)

        # Config.
        config_sizer = wx.FlexGridSizer(rows=1, cols=2,  vgap=5, hgap=5)
        config_sizer.AddGrowableCol(1, 1)
        panel_box.Add(config_sizer, proportion=1, flag=wx.EXPAND)

        # Values.
        config_sizer.Add(wx.StaticText(self, label='Values:'),
                         flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.ALL, border=5)
        self.values_input = wx.TextCtrl(self)
        config_sizer.Add(self.values_input, flag=wx.EXPAND | wx.ALL, border=5)

        self.SetSizerAndFit(panel_box)

    def GetValue(self):
        raw_values = self.values_input.Value.split(',')

        # Ensure the values are sane.
        try:
            values = [float(x) for x in raw_values]
        except ValueError as e:
            raise ValueError('Invalid value: {0}'.format(str(e)))

        return ArbitraryConfig(values)

    def SetValue(self, config):
        self.values_input.Value = ', '.join(
            '{0:n}'.format(x) for x in config.values)

# New config panel for getting arbitary variable values from CSV.


class FileConfigPanel(wx.Panel):
    def __init__(self, parent, *args, **kwargs):
        wx.Panel.__init__(self, parent, *args, **kwargs)

        # Make parent attribute of FileConfigPanel to play nice with MessageDialog
        self.parent = parent

        # Panel.
        panel_box = wx.BoxSizer(wx.VERTICAL)

        # Table for csv data from spacq.gui.display.table.generic
        self.table = VirtualListCtrl(self)
        self.table.Hide()

        self.column_names = []

        # Config.
        config_sizer = wx.GridBagSizer(3, 2)
        panel_box.Add(config_sizer, proportion=1, flag=wx.EXPAND)

        # Load button
        load_button = wx.Button(self, wx.ID_OPEN, label='Load CSV')
        # TODO: write method for file selection
        load_button.Bind(wx.EVT_BUTTON, self.OnMenuFileOpen)
        config_sizer.Add(load_button, pos=(0, 0),
                         flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.ALL, border=5)
        # File name display
        self.csv_address = ''
        self.csv_filename = wx.StaticText(self, label=self.csv_address)
        config_sizer.Add(self.csv_filename, pos=(
            0, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALL, border=5)

        # Variable select
        config_sizer.Add(wx.StaticText(self, label='Select Column:'), pos=(1, 0),
                         flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.ALL, border=5)
        # Display column names
        self.variable_list = wx.ListBox(
            self, size=wx.Size(200, 100), choices=self.column_names)
        self.Bind(wx.EVT_LISTBOX, self.OnAxisSelection, self.variable_list)
        config_sizer.Add(self.variable_list, pos=(1, 1), flag=wx.ALL, border=5)

        # Values.
        # TODO: add enable/disable for needing csv selected first
        config_sizer.Add(wx.StaticText(self, label='Values:'), pos=(2, 0),
                         flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.ALL, border=5)
        # TODO: find wx box that allows overflow
        self.value_bar = wx.StaticText(self, label='No CSV column selected.',
                                       style=wx.ST_NO_AUTORESIZE)
        config_sizer.Add(self.value_bar, pos=(
            2, 1), flag=wx.ST_NO_AUTORESIZE | wx.ALL, border=5)

        self.SetSizerAndFit(panel_box)

    # TODO: return to finishing this up or what not
    # From math_setup for data explorer function for callback
    def OnAxisSelection(self, evt=None):
        # Get what list index was selected
        if self.variable_list.Selection == wx.NOT_FOUND:
            resultIndex = None
        else:
            resultIndex = self.variable_list.Selection

        # Retrieve table data, and select chosen column
        headings, rows, types = self.table.GetValue(types=['scalar'])

        # Ensure the values are sane, because types is only determined off first entries.
        try:
            self.values_input = [float(x) for x in rows[:, resultIndex]]
        except ValueError as e:
            # not really working
            MessageDialog(self.parent, str(
                e), 'Invalid value: {0}'.format(str(e)))
            return

        # Formatting to remove newlines that numpy will add into array for printing
        valuesLabel = str(self.values_input)[1:-1].replace('\n', ' ')

        # Display string of list
        self.value_bar.SetLabel(valuesLabel)

    # loads csv and adds headers and data to self.object
    def OnMenuFileOpen(self, evt=None):
        try:
            result = load_csv(self.parent)
        except IOError as e:
            # May need to be self.parent if this error ever gets called
            MessageDialog(self.panel_box, str(e), 'Could not load data').Show()
            return

        has_header, values, filename = result

        # TODO: load_csv will return has_header for first line being data
        # not what wanted. Come back later
        # If has_header is True, the first row becomes column names

        if has_header:
            headers, rows = values[0], array(values[1:])
        else:
            headers, rows = [''] * len(values[0]), array(values)
        # Ensure that all columns have a header.
        for i, header in enumerate(headers):
            if not header:
                headers[i] = 'Column {0}'.format(i + 1)

        # put filename and column variables into update display
        self.csv_address = filename
        self.column_names = headers
        self.csv_filename.SetLabel(self.csv_address)
        self.variable_list.Set(self.column_names)

        # put header names and data in the self.table for VirtualListCtrl
        self.table.SetValue(headers, rows)
    ###############################################

    # Regular Get and Set that finally set variables
    def GetValue(self):
        raw_values = self.values_input

        # Ensure the values are sane.
        try:
            values = [float(x) for x in raw_values]
        except ValueError as e:
            raise ValueError('Invalid value: {0}'.format(str(e)))

        return ArbitraryConfig(values)

    def SetValue(self, config):
        self.values_input.Value = ', '.join(
            '{0:n}'.format(x) for x in config.values)


class ConditionEditor(Dialog):
    def __init__(self, parent, ok_callback, *args, **kwargs):
        kwargs['style'] = kwargs.get(
            'style', wx.DEFAULT_DIALOG_STYLE) | wx.RESIZE_BORDER

        Dialog.__init__(self, parent, *args, **kwargs)

        self.ok_callback = ok_callback

        # Dialog.
        dialog_box = wx.BoxSizer(wx.VERTICAL)

        # Condition Editor

        condition_static_box = wx.StaticBox(self, label='Condition')
        condition_box = wx.StaticBoxSizer(condition_static_box, wx.HORIZONTAL)
        dialog_box.Add(condition_box)

        # Left Argument

        left_arg_box = wx.BoxSizer(wx.VERTICAL)
        condition_box.Add(left_arg_box)
        left_arg_input = wx.TextCtrl(self, size=(150, -1))
        left_arg_box.Add(left_arg_input)

        # Operator

        operators = ['<', '==', '!=', '>']
        self.op_menu = wx.ComboBox(
            self, choices=operators, style=wx.CB_READONLY, size=(70, -1))
        self.op_menu.SetStringSelection(operators[0])
        condition_box.Add(self.op_menu)

        # Right Argument

        right_arg_box = wx.BoxSizer(wx.VERTICAL)
        condition_box.Add(right_arg_box)
        right_arg_input = wx.TextCtrl(self, size=(150, -1))
        right_arg_box.Add(right_arg_input)

        self.args = [left_arg_input, right_arg_input]
        arg_boxes = [left_arg_box, right_arg_box]

        # Type.

        # This loop setup is a bit messy coding.
        self.arg_type_setters = []
        self.units_input = []
        for i in range(0, 2):
            type_static_box = wx.StaticBox(
                self, label='Argument {0}'.format(i+1))
            type_box = wx.StaticBoxSizer(type_static_box, wx.VERTICAL)
            arg_boxes[i].Add(type_box, flag=wx.CENTER | wx.ALL, border=5)

            types = {}

            types['float'] = wx.RadioButton(
                self, label='Float', style=wx.RB_GROUP)
            type_box.Add(types['float'], flag=wx.ALIGN_LEFT | wx.ALL, border=5)

            types['integer'] = wx.RadioButton(self, label='Integer')
            type_box.Add(types['integer'],
                         flag=wx.ALIGN_LEFT | wx.ALL, border=5)

            types['string'] = wx.RadioButton(self, label='String')
            type_box.Add(types['string'],
                         flag=wx.ALIGN_LEFT | wx.ALL, border=5)

            types['resource name'] = wx.RadioButton(self, label='Resource')
            type_box.Add(types['resource name'],
                         flag=wx.ALIGN_LEFT | wx.ALL, border=5)

            # Units.
            types['quantity'] = wx.RadioButton(self, label='Quantity')
            type_box.Add(types['quantity'], flag=wx.CENTER)

            self.arg_type_setters.append(types)

        # End buttons.
        button_box = wx.BoxSizer(wx.HORIZONTAL)
        dialog_box.Add(button_box, flag=wx.CENTER | wx.ALL, border=5)

        ok_button = wx.Button(self, wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, self.OnOk, ok_button)
        button_box.Add(ok_button)

        cancel_button = wx.Button(self, wx.ID_CANCEL)
        button_box.Add(cancel_button)

        self.SetSizerAndFit(dialog_box)

    def OnOk(self, evt=None):
        if self.ok_callback(self):
            self.Destroy()

    def SetValue(self, condition):
        self.arg_type_setters[0][condition.type1].Value = True
        self.arg_type_setters[1][condition.type2].Value = True
        self.args[0].Value = str(condition.arg1)
        self.args[1].Value = str(condition.arg2)
        self.op_menu.SetStringSelection(condition.op_symbol)

    def GetValue(self):
        cond_args = []
        arg_types = []
        for i, type in enumerate(self.arg_type_setters):
            # We ensure values are sane along the way.
            if type['float'].Value:
                arg_types.append('float')
                cond_args.append(float(self.args[i].Value))
            elif type['integer'].Value:
                arg_types.append('integer')
                cond_args.append(int(self.args[i].Value))
            elif type['resource name'].Value:
                arg_types.append('resource name')
                cond_args.append(self.args[i].Value)
            elif type['quantity'].Value:
                arg_types.append('quantity')
                cond_args.append(Quantity(self.args[i].Value))
            elif type['string'].Value:
                arg_types.append('string')
                cond_args.append(self.args[i].Value)

        condition = Condition(
            arg_types[0], arg_types[1], cond_args[0], self.op_menu.Value, cond_args[1])

        return condition


class ConditionVariableEditor(Dialog):
    col_conditions = VariableColumnDefn(title='Condition', valueGetter=lambda x: str(x),
                                        isSpaceFilling=True, align='left')

    def __init__(self, parent, ok_callback, *args, **kwargs):
        kwargs['style'] = kwargs.get(
            'style', wx.DEFAULT_DIALOG_STYLE) | wx.RESIZE_BORDER

        Dialog.__init__(self, parent, *args, **kwargs)

        self.ok_callback = ok_callback

        # Dialog.
        dialog_box = wx.BoxSizer(wx.VERTICAL)
        dialog_box.SetMinSize((350, 200))

        # List (left op, op, right op).

        # OLV.
        self.condition_olv = ObjectListView.FastObjectListView(self)
        dialog_box.Add(self.condition_olv, proportion=1,
                       flag=wx.ALL | wx.EXPAND)

        self.condition_olv.SetColumns([self.col_conditions])

        self.condition_olv.cellEditMode = self.condition_olv.CELLEDIT_DOUBLECLICK
        self.condition_olv.Bind(
            ObjectListView.EVT_CELL_EDIT_STARTING, self.OnCellEditStarting)

        row_box = wx.BoxSizer(wx.HORIZONTAL)
        dialog_box.Add(row_box, proportion=0, flag=wx.ALL | wx.CENTER)

        # Add Condition.
        add_button = wx.Button(self, wx.ID_ADD)
        self.Bind(wx.EVT_BUTTON, self.OnAddCondition, add_button)
        row_box.Add(add_button)

        # Remove Condition.
        remove_button = wx.Button(self, wx.ID_REMOVE)
        remove_button.Bind(wx.EVT_BUTTON, self.OnRemoveConditions)
        row_box.Add(remove_button)

        # End buttons.
        button_box = wx.BoxSizer(wx.HORIZONTAL)
        dialog_box.Add(button_box, flag=wx.CENTER | wx.ALL, border=5)

        ok_button = wx.Button(self, wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, self.OnOk, ok_button)
        button_box.Add(ok_button)

        cancel_button = wx.Button(self, wx.ID_CANCEL)
        button_box.Add(cancel_button)

        self.SetSizerAndFit(dialog_box)

    def GetValue(self):
        conditions = self.condition_olv.GetObjects()

        # Get the resource_names from the conditions.
        resource_names = []
        for condition in conditions:
            if condition.type1 == 'resource name':
                resource_names.append(condition.arg1)
            if condition.type2 == 'resource name':
                resource_names.append(condition.arg2)

        return resource_names, conditions

    def SetValue(self, resource_names, conditions):

        self.condition_olv.SetObjects(conditions)

    def OnOk(self, evt=None):
        if self.ok_callback(self):
            self.Destroy()

    def OnAddCondition(self, evt=None):
        """
        Add a condition to the listctrl
        """

        def ok_callback(dlg):
            try:
                self.condition_olv.AddObject(dlg.GetValue())
            except ValueError as e:
                MessageDialog(self, str(e), 'Invalid value').Show()
                return False

            # OLV likes to select a random item at this point.
            self.condition_olv.DeselectAll()
            return True

        # Start up the new dialog.
        dlg = ConditionEditor(self, ok_callback, title='Condition Editor')
        dlg.Show()

    def OnRemoveConditions(self, evt=None):
        """
        Remove all selected conditions from the OLV.
        """

        selected = self.condition_olv.GetSelectedObjects()

        if selected:
            self.condition_olv.RemoveObjects(selected)

    def OnCellEditStarting(self, evt):
        condition = evt.rowModel

        # Ignore frivolous requests.
        if evt.rowIndex < 0:
            evt.Veto()
            return

        def ok_callback(dlg):
            try:
                value = dlg.GetValue()
            except ValueError as e:
                MessageDialog(self, str(e), 'Invalid value').Show()
                return False

            condition.type1 = value.type1
            condition.type2 = value.type2
            condition.arg1 = value.arg1
            condition.arg2 = value.arg2
            condition.op_symbol = value.op_symbol
            return True

        dlg = ConditionEditor(self, ok_callback, title='Condition Editor')
        dlg.SetValue(condition)
        dlg.Show()

        # No need to use the default editor.
        evt.Veto()


class OutputVariableEditor(Dialog):
    def __init__(self, parent, ok_callback, *args, **kwargs):
        kwargs['style'] = kwargs.get(
            'style', wx.DEFAULT_DIALOG_STYLE) | wx.RESIZE_BORDER

        Dialog.__init__(self, parent, *args, **kwargs)

        self.ok_callback = ok_callback

        # Dialog.
        dialog_box = wx.BoxSizer(wx.VERTICAL)

        # Config.
        self.config_notebook = wx.Notebook(self)
        dialog_box.Add(self.config_notebook, proportion=1,
                       flag=wx.EXPAND | wx.ALL, border=5)

        self.config_panel_types = []

        # Linear.
        linspace_config_panel = LinSpaceConfigPanel(self.config_notebook)
        self.config_panel_types.append(LinSpaceConfig)
        self.config_notebook.AddPage(linspace_config_panel, 'Linear')

        # Arbitrary.
        arbitrary_config_panel = ArbitraryConfigPanel(self.config_notebook)
        self.config_panel_types.append(ArbitraryConfig)
        self.config_notebook.AddPage(arbitrary_config_panel, 'Arbitrary')

        # File load
        file_config_panel = FileConfigPanel(self.config_notebook)
        self.config_panel_types.append(ArbitraryConfig)
        self.config_notebook.AddPage(file_config_panel, 'From File')

        # Smooth set.
        smooth_static_box = wx.StaticBox(self, label='Smooth set')
        smooth_box = wx.StaticBoxSizer(smooth_static_box, wx.HORIZONTAL)
        dialog_box.Add(smooth_box, flag=wx.CENTER | wx.ALL, border=5)

        smooth_box.Add(wx.StaticText(self, label='Steps:'), flag=wx.CENTER)

        self.smooth_steps_input = wx.SpinCtrl(self, min=1, initial=100)
        smooth_box.Add(self.smooth_steps_input,
                       flag=wx.CENTER | wx.ALL, border=5)

        self.smooth_from_checkbox = wx.CheckBox(self, label='From const')
        smooth_box.Add(self.smooth_from_checkbox,
                       flag=wx.CENTER | wx.ALL, border=5)

        self.smooth_to_checkbox = wx.CheckBox(self, label='To const')
        smooth_box.Add(self.smooth_to_checkbox,
                       flag=wx.CENTER | wx.ALL, border=5)

        self.smooth_transition_checkbox = wx.CheckBox(self, label='Transition')
        smooth_box.Add(self.smooth_transition_checkbox,
                       flag=wx.CENTER | wx.ALL, border=5)

        # Type.
        type_static_box = wx.StaticBox(self, label='Type')
        type_box = wx.StaticBoxSizer(type_static_box, wx.HORIZONTAL)
        dialog_box.Add(type_box, flag=wx.CENTER | wx.ALL, border=5)

        self.type_float = wx.RadioButton(
            self, label='Float', style=wx.RB_GROUP)
        type_box.Add(self.type_float, flag=wx.CENTER | wx.ALL, border=5)

        self.type_integer = wx.RadioButton(self, label='Integer')
        type_box.Add(self.type_integer, flag=wx.CENTER | wx.ALL, border=5)

        # Units.
        quantity_static_box = wx.StaticBox(self, label='Quantity')
        quantity_box = wx.StaticBoxSizer(quantity_static_box, wx.HORIZONTAL)
        type_box.Add(quantity_box)

        self.type_quantity = wx.RadioButton(self)
        quantity_box.Add(self.type_quantity, flag=wx.CENTER)

        self.units_input = wx.TextCtrl(self)
        quantity_box.Add(self.units_input)

        # End buttons.
        button_box = wx.BoxSizer(wx.HORIZONTAL)
        dialog_box.Add(button_box, flag=wx.CENTER | wx.ALL, border=5)

        ok_button = wx.Button(self, wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, self.OnOk, ok_button)
        button_box.Add(ok_button)

        cancel_button = wx.Button(self, wx.ID_CANCEL)
        button_box.Add(cancel_button)

        self.SetSizerAndFit(dialog_box)

    def GetValue(self):
        if self.type_float.Value:
            type = 'float'
            units = None
        elif self.type_integer.Value:
            type = 'integer'
            units = None
        else:
            type = 'quantity'
            units = self.units_input.Value

            # Ensure that the units are valid.
            Quantity(1, units)

        return (self.config_notebook.CurrentPage.GetValue(), self.smooth_steps_input.Value,
                self.smooth_from_checkbox.Value, self.smooth_to_checkbox.Value,
                self.smooth_transition_checkbox.Value, type, units)

    def SetValue(self, config, smooth_steps, smooth_from, smooth_to, smooth_transition, type, units):
        config_type = self.config_panel_types.index(config.__class__)
        self.config_notebook.ChangeSelection(config_type)
        self.config_notebook.CurrentPage.SetValue(config)

        (self.smooth_steps_input.Value, self.smooth_from_checkbox.Value,
         self.smooth_to_checkbox.Value,
         self.smooth_transition_checkbox.Value) = smooth_steps, smooth_from, smooth_to, smooth_transition

        if type == 'float':
            self.type_float.Value = True
        elif type == 'integer':
            self.type_integer.Value = True
        else:
            self.type_quantity.Value = True
            self.units_input.Value = units if units is not None else ''

    def OnOk(self, evt=None):
        if self.ok_callback(self):
            self.Destroy()


class VariablesPanel(wx.Panel):
    col_name = VariableColumnDefn(checkStateGetter='enabled', title='Name', valueGetter='name',
                                  width=150, align='left')
    col_order = VariableColumnDefn(title='#', valueGetter='order', width=40)
    col_resource = VariableColumnDefn(title='Resource', valueGetter='resource_name',
                                      width=150, align='left')
    col_values = VariableColumnDefn(title='Values', valueGetter=lambda x: str(x),
                                    isSpaceFilling=True, align='left')
    col_wait = VariableColumnDefn(title='Wait time', valueGetter='wait')
    col_const = VariableColumnDefn(checkStateGetter='use_const', title='Const. value',
                                   valueGetter='const')

    def __init__(self, parent, global_store, *args, **kwargs):
        wx.Panel.__init__(self, parent, *args, **kwargs)

        self.global_store = global_store

        # Panel.
        panel_box = wx.BoxSizer(wx.VERTICAL)

        # OLV.
        self.olv = ObjectListView.GroupListView(self)
        panel_box.Add(self.olv, proportion=1, flag=wx.ALL | wx.EXPAND)

        self.olv.SetColumns([self.col_name, self.col_order, self.col_resource, self.col_values,
                             self.col_wait, self.col_const])
        self.olv.SetSortColumn(self.col_order)

        self.olv.cellEditMode = self.olv.CELLEDIT_DOUBLECLICK
        self.olv.Bind(ObjectListView.EVT_CELL_EDIT_STARTING,
                      self.OnCellEditStarting)
        self.olv.Bind(ObjectListView.EVT_CELL_EDIT_FINISHING,
                      self.OnCellEditFinishing)
        self.olv.Bind(ObjectListView.EVT_CELL_EDIT_FINISHED,
                      self.OnCellEditFinished)

        # Buttons.
        button_box = wx.BoxSizer(wx.HORIZONTAL)
        panel_box.Add(button_box, proportion=0, flag=wx.ALL | wx.CENTER)

        # Row buttons.
        row_box = wx.BoxSizer(wx.HORIZONTAL)
        button_box.Add(row_box, flag=wx.LEFT, border=20)

        add_button = wx.Button(self, wx.ID_ADD, label='Add Output')
        add_button.Bind(wx.EVT_BUTTON, self.OnAddVariable)
        row_box.Add(add_button)

        add_cond_button = wx.Button(self, wx.ID_ADD, label='Add Condition')
        add_cond_button.Bind(wx.EVT_BUTTON, self.OnAddConditionVariable)
        row_box.Add(add_cond_button)

        remove_button = wx.Button(self, wx.ID_REMOVE)
        remove_button.Bind(wx.EVT_BUTTON, self.OnRemoveVariables)
        row_box.Add(remove_button)

        # Export buttons.
        export_box = wx.BoxSizer(wx.HORIZONTAL)
        button_box.Add(export_box, flag=wx.LEFT, border=20)

        save_button = wx.Button(self, wx.ID_SAVE, label='Save...')
        save_button.Bind(wx.EVT_BUTTON, self.OnSave)
        export_box.Add(save_button)

        load_button = wx.Button(self, wx.ID_OPEN, label='Load...')
        load_button.Bind(wx.EVT_BUTTON, self.OnLoad)
        export_box.Add(load_button)

        self.SetSizer(panel_box)

    def max_order(self):
        """
        Find the highest-used order in the OLV.
        """

        try:
            return max(x.order for x in self.olv.GetObjects())
        except ValueError:
            return 0

    def OnCellEditStarting(self, evt):
        col = evt.objectListView.columns[evt.subItemIndex]
        var = evt.rowModel

        # Ignore frivolous requests.
        if evt.rowIndex < 0:
            evt.Veto()
            return

        if col == self.col_values:
            def ok_callback(dlg):
                try:
                    values = dlg.GetValue()
                except ValueError as e:
                    MessageDialog(self, str(e), 'Invalid value').Show()
                    return False

                for i, name in enumerate(var.editor_parameters):
                    setattr(var, name, values[i])

                return True

            editor = var.editor
            dlg = editor(self, ok_callback, title=var.name)
            dlg.SetValue(*[getattr(var, attr)
                         for attr in var.editor_parameters])

            dlg.Show()

            # No need to use the default editor.
            evt.Veto()

        elif col == self.col_const:
            # We replace the editor with float editor, as ObjectListView picks the first entry by default
            # in the column as what defines the editor.
            evt.editor = ObjectListView.CellEditor.FloatEditor(
                self.olv, evt.subItemIndex)

        # if there is something non-editable, we cancel the edit.
        if col.valueGetter in var.edit_restrictions:
            evt.Veto()

    def OnCellEditFinishing(self, evt):
        col = evt.objectListView.columns[evt.subItemIndex]

        if col == self.col_name:
            var = evt.rowModel  # With old name.
            var_new_name = evt.editor.Value

            if var_new_name == var.name:
                # Not actually changed.
                return

            # Attempt to add a new entry first.
            try:
                self.global_store.variables[var_new_name] = var.variable
            except KeyError:
                MessageDialog(self, var_new_name,
                              'Variable name conflicts').Show()
                evt.Veto()
                return

            # Remove the old entry.
            del self.global_store.variables[var.name]

        elif col == self.col_order:
            try:
                order_new = round(float(evt.editor.Value)) # Entry in cell (i.e. order to be set)
                order = evt.rowModel  # With old order
                if order_new == order.order:
                # Not actually changed.
                    return
                else:
                    order.order = order_new
            except ValueError:
                pass # Assumed not an int was given in this cell

    def OnCellEditFinished(self, evt):
        col = evt.objectListView.columns[evt.subItemIndex]

        if col == self.col_order:
            self.olv.SetObjects(self.olv.GetObjects())
            self.olv.RebuildGroups()

    def OnSave(self, evt=None):
        """
        Save all the rows in the OLV.
        """

        try:
            save_pickled(self, [var.variable for var in self.olv.GetObjects(
            )], extension='var', file_type='Variables')
        except IOError as e:
            MessageDialog(self, str(e), 'Save error').Show()
            return

    def OnLoad(self, evt=None):
        """
        Load some rows to the OLV.
        """

        try:
            values = load_pickled(self, extension='var', file_type='Variables')
        except IOError as e:
            MessageDialog(self, str(e), 'Load error').Show()
            return

        if values is not None:
            # Clear the OLV.
            for var in self.olv.GetObjects():
                del self.global_store.variables[var.name]
                self.olv.RemoveObject(var)

            conflicting_names = []
            for var in values:
                try:
                    self.global_store.variables[var.name] = var.variable
                except KeyError:
                    conflicting_names.append(var.name)
                    continue

                self.olv.AddObject(var)

            if conflicting_names:
                MessageDialog(self, ', '.join(conflicting_names),
                              'Variable names conflict').Show()

    def OnAddVariable(self, evt=None):
        """
        Add a blank variable to the OLV.
        """

        # Ensure that we get a unique name.
        with self.global_store.variables.lock:
            num = 1
            done = False
            while not done:
                name = 'New variable {0}'.format(num)
                var = OutputVariable(name=name, order=self.max_order()+1)

                try:
                    self.global_store.variables[name] = var
                except KeyError:
                    num += 1
                else:
                    done = True

        guivar = GuiVariable(var, 'output')
        self.olv.AddObject(guivar)

        # OLV likes to select a random item at this point.
        self.olv.DeselectAll()

    def OnAddConditionVariable(self, evt=None):
        """
        Add a blank conditional variable to the OLV.
        """

        with self.global_store.variables.lock:
            num = 1
            done = False
            while not done:
                name = 'New condition {0}'.format(num)
                var = ConditionVariable(name=name, order=self.max_order()+1)

                try:
                    self.global_store.variables[name] = var
                except KeyError:
                    num += 1
                else:
                    done = True

        guivar = GuiVariable(var, 'condition')
        self.olv.AddObject(guivar)

        # OLV likes to select a random item at this point.
        self.olv.DeselectAll()

    def OnRemoveVariables(self, evt=None):
        """
        Remove all selected variables from the OLV.
        """

        selected = self.olv.GetSelectedObjects()

        if selected:
            self.olv.RemoveObjects(selected)

        for row in selected:
            del self.global_store.variables[row.name]


class GuiVariable(object):
    """
    Wraps variables for displaying in the ObjectListView.
    This variable will act like the wrapped variable, but will also contain attributes
    describing how the values should be edited.
    If the variable doesn't have the attribute, then this class creates that attribute
    and assigns it a value of 'N/A'.
    """

    def __init__(self, var, vartype):

        # Make the gui variable quack like the wrapped variable.
        self.__class__ = type(var.__class__.__name__,
                              (self.__class__, var.__class__),
                              {})
        self.__dict__ = var.__dict__

        self.variable = var
        self._allowed_types = set(['condition', 'output'])
        self.edit_restrictions = []

        if vartype not in self._allowed_types:
            raise ValueError('Invalid variable type: {0}'.format(type))

        # Depending on the type of variable, how the variable is displayed and edited is defined below.
        if vartype == 'condition':
            self.editor = ConditionVariableEditor
            self.editor_parameters = ('resource_names', 'conditions')

            # columns that condition variables DONT have.
            self.edit_restrictions.append('const')
            self.edit_restrictions.append('resource_name')

        elif vartype == 'output':
            self.editor = OutputVariableEditor
            self.editor_parameters = ('config', 'smooth_steps', 'smooth_from',
                                      'smooth_to', 'smooth_transition',
                                      'type', 'units')

    def __getattr__(self, name):
        # If the gui variable doesn't have the attribute, then create the attribute
        # with a value of 'N/A', and return its value.
        setattr(self, name, 'N/A')
        return getattr(self, name)
