import wx
import wx.lib.scrolledpanel as scrolled

"""
An interface for defining virtual swept variables and writing to
real resources.
"""
class MultipleVariableConfigPanel(scrolled.ScrolledPanel):
    def __init__(self, parent, *args, **kwargs):
        scrolled.ScrolledPanel.__init__(self, parent, -1, style=wx.HSCROLL, *args, **kwargs)

        self.initial_var_count = 4

        # Panel

        self.scrolled_panel = scrolled.ScrolledPanel(self,-1,
                    style = wx.TAB_TRAVERSAL|wx.SUNKEN_BORDER, name='scroll panel')
        self.scrolled_panel.SetAutoLayout(1)
        self.scrolled_panel.SetupScrolling()

        multiple_static_box = wx.StaticBox(self, label= 'Virtual Variable Setup')

        self.panel_box = wx.StaticBoxSizer(multiple_static_box,wx.VERTICAL)

        count_setup = wx.BoxSizer(wx.HORIZONTAL)
        self.panel_box.Add(count_setup, flag=wx.ALL, border=5)

        label = wx.StaticText(self, label='Number of Virtual Variables')
        self.var_count = wx.SpinCtrl(self, min=1, initial=2, max=100)
        button = wx.Button(self, label='Update')
        self.Bind(wx.EVT_BUTTON, self.OnUpdate, button)

        count_setup.Add(label,flag=wx.ALL, border=5)
        count_setup.Add(self.var_count, flag=wx.ALL, border=5)
        count_setup.Add(button, flag=wx.ALL, border=5)

        # Class attribute so can add to in OnUpdate
        self.value_setup = wx.BoxSizer(wx.HORIZONTAL)
        self.panel_box.Add(self.value_setup, flag=wx.ALL, border=5)

        # Labels for virtual variable inputs
        label_setup = wx.BoxSizer(wx.VERTICAL)
        label_setup.AddSpacer(5)
        label_setup.Add(wx.StaticText(self, label='Name'),
                flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, border=5)
        label_setup.AddSpacer(8)
        label_setup.Add(wx.StaticText(self, label='Initial:'),
                flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, border=5)
        label_setup.AddSpacer(8)
        label_setup.Add(wx.StaticText(self, label='Final:'),
                flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, border=5)
        label_setup.AddSpacer(8)
        label_setup.Add(wx.StaticText(self, label='Steps:'),
                flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, border=5)
        label_setup.AddSpacer(8)
        label_setup.Add(wx.StaticText(self, label='Order:'),
                flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, border=5)
        self.value_setup.Add(label_setup, flag=wx.EXPAND|wx.ALL, border=5)

        # for i in range(0,self.variable_count.GetValue()):
        self.name_value = [None]*self.initial_var_count
        self.start_value = [None]*self.initial_var_count
        self.end_value = [None]*self.initial_var_count
        self.step_value = [None]*self.initial_var_count
        self.order_value = [None]*self.initial_var_count

        for i in range(0,self.initial_var_count):
            mini_setup = wx.BoxSizer(wx.VERTICAL)
            self.name_value[i] = wx.TextCtrl(self, value="VirtVar{0}".format(i))
            mini_setup.Add(self.name_value[i], flag=wx.EXPAND|wx.ALL, border=5)
            self.start_value[i] = wx.TextCtrl(self, value="1")
            mini_setup.Add(self.start_value[i], flag=wx.EXPAND|wx.ALL, border=5)
            self.end_value[i] = wx.TextCtrl(self, value="2")
            mini_setup.Add(self.end_value[i], flag=wx.EXPAND|wx.ALL, border=5)
            self.step_value[i] = wx.SpinCtrl(self, min=1, initial=3, max=int(1e9))
            mini_setup.Add(self.step_value[i], flag=wx.EXPAND|wx.ALL, border=5)
            self.order_value[i] = wx.SpinCtrl(self, min=1, initial=1, max=int(1e9))
            mini_setup.Add(self.order_value[i], flag=wx.EXPAND|wx.ALL, border=5)

            self.value_setup.Add(mini_setup, flag=wx.EXPAND|wx.ALL, border=5)

        self.SetSizerAndFit(self.panel_box)
        self.SetupScrolling(scroll_y = False)

    def OnUpdate(self, evt=None):
        EnableCount = self.var_count.Value

        # Adding more than initially setup with
        if EnableCount > self.initial_var_count:
            for i in range(self.initial_var_count,EnableCount):
                self.name_value.append(wx.TextCtrl(self, value="VirtVar{0}".format(i)))
                self.start_value.append(wx.TextCtrl(self, value="1"))
                self.end_value.append(wx.TextCtrl(self, value="2"))
                self.step_value.append(wx.SpinCtrl(self, min=1, initial=3, max=int(1e9)))
                self.order_value.append(wx.SpinCtrl(self, min=1, initial=1, max=int(1e9)))

                mini_setup = wx.BoxSizer(wx.VERTICAL)
                mini_setup.Add(self.name_value[i], flag=wx.EXPAND|wx.ALL, border=5)
                mini_setup.Add(self.start_value[i], flag=wx.EXPAND|wx.ALL, border=5)
                mini_setup.Add(self.end_value[i], flag=wx.EXPAND|wx.ALL, border=5)
                mini_setup.Add(self.step_value[i], flag=wx.EXPAND|wx.ALL, border=5)
                mini_setup.Add(self.order_value[i], flag=wx.EXPAND|wx.ALL, border=5)

                self.value_setup.Add(mini_setup, flag=wx.EXPAND|wx.ALL, border=5)

            # self.SetSizerAnd(self.panel_box)
            # self.SetSizerAndFit(self.panel_box)
            self.Layout()
            self.SetupScrolling(scroll_y = False)

            self.initial_var_count = EnableCount

        for i in range(0,EnableCount):
            self.name_value[i].Show()
            self.start_value[i].Show()
            self.end_value[i].Show()
            self.step_value[i].Show()
            self.order_value[i].Show()
        for i in range(EnableCount,self.initial_var_count):
            self.name_value[i].Hide()
            self.start_value[i].Hide()
            self.end_value[i].Hide()
            self.step_value[i].Hide()
            self.order_value[i].Hide()

        # self.SetSizerAndFit(self.panel_box)

    def GetValue(self):
        try:
            starts = [float(x.Value) for x in self.start_value]
        except ValueError:
            raise ValueError('Invalid initial value.')
        try:
            ends = [float(x.Value) for x in self.end_value]
        except ValueError:
            raise ValueError('Invalid initial value.')

        names = [x.Value for x in self.name_value]
        steps = [x.Value for x in self.step_value]
        orders = [x.Value for x in self.order_value]

        return names, starts, ends, steps, orders


    def GetValue(self):
        try:
            starts = [float(x.Value) for x in self.start_value]
        except ValueError:
            raise ValueError('Invalid initial value.')
        try:
            ends = [float(x.Value) for x in self.end_value]
        except ValueError:
            raise ValueError('Invalid initial value.')

        names = [x.Value for x in self.name_value]
        steps = [x.Value for x in self.step_value]
        orders = [x.Value for x in self.order_value]

        return names, starts, ends, steps, orders


class DependentVariableConfigPanel(scrolled.ScrolledPanel):
    def __init__(self, parent, *args, **kwargs):
        scrolled.ScrolledPanel.__init__(self, parent, -1, style=wx.VSCROLL, *args, **kwargs)

        self.scrolled_panel = scrolled.ScrolledPanel(self,-1,
                    style = wx.TAB_TRAVERSAL|wx.SUNKEN_BORDER, name='scroll panel')
        self.scrolled_panel.SetAutoLayout(1)
        self.scrolled_panel.SetupScrolling()


        static_box = wx.StaticBox(self, label='Dependent Variable Setup')
        static_panel_box = wx.StaticBoxSizer(static_box, wx.VERTICAL)

        count_setup = wx.BoxSizer(wx.HORIZONTAL)
        static_panel_box.Add(count_setup, flag=wx.ALL, border=5)

        label = wx.StaticText(self, label='Number of Dependent Variables')
        self.dependent_count = wx.SpinCtrl(self, min=1, initial=2, max=100)
        button = wx.Button(self, label='Update')
        self.Bind(wx.EVT_BUTTON, self.OnUpdate, button)

        count_setup.Add(label, flag=wx.ALL, border = 5)
        count_setup.Add(self.dependent_count, flag=wx.ALL, border = 5)
        count_setup.Add(button, flag=wx.ALL, border = 5)

        self.initial_var_count = 6

        # panel_box = wx.FlexGridSizer(3,2)
        panel_box = wx.BoxSizer(wx.HORIZONTAL)
        self.left_box = wx.BoxSizer(wx.VERTICAL)
        self.right_box = wx.BoxSizer(wx.VERTICAL)

        self.name_value = [None]*self.initial_var_count
        self.expression_value = [None]*self.initial_var_count
        self.equal_bar = [None]*self.initial_var_count
        self.enable = [True]*self.initial_var_count

        for i in range(0,self.initial_var_count):
            unit_box = wx.BoxSizer(wx.HORIZONTAL)
            self.name_value[i] = wx.TextCtrl(self, value="RealVar{0}".format(i))
            unit_box.Add(self.name_value[i], flag=wx.EXPAND|wx.ALL, border=5)
            self.equal_bar[i] = wx.StaticText(self, label=' = ')
            unit_box.Add(self.equal_bar[i], flag=wx.ALL)
            self.expression_value[i] = wx.TextCtrl(self)
            unit_box.Add(self.expression_value[i], flag=wx.EXPAND|wx.ALL, border=5)

            # Alternate left and right boxs
            if i % 2 == 0:
                self.left_box.Add(unit_box, flag=wx.EXPAND|wx.ALL, border=5)
            else:
                self.right_box.Add(unit_box, flag=wx.EXPAND|wx.ALL, border=5)

        panel_box.Add(self.left_box, flag=wx.EXPAND|wx.ALL, border=5)
        panel_box.Add(self.right_box, flag=wx.EXPAND|wx.ALL, border=5)

        static_panel_box.Add(panel_box, flag=wx.EXPAND|wx.ALL, border=5)
        self.SetSizerAndFit(static_panel_box)
        self.SetupScrolling(scroll_x = False)

    def OnUpdate(self, evt=None):
        EnableCount = self.dependent_count.Value

        # Add entries to store
        if EnableCount > self.initial_var_count:
            for i in range(self.initial_var_count, EnableCount):
                # Add to the lists
                self.name_value.append(wx.TextCtrl(self, value="RealVar{0}".format(i)))
                self.equal_bar.append(wx.StaticText(self, label=' = '))
                self.expression_value.append(wx.TextCtrl(self))
                self.enable.append(True)

                unit_box = wx.BoxSizer(wx.HORIZONTAL)
                unit_box.Add(self.name_value[i], flag=wx.EXPAND|wx.ALL, border=5)
                unit_box.Add(self.equal_bar[i], flag=wx.ALL)
                unit_box.Add(self.expression_value[i], flag=wx.EXPAND|wx.ALL, border=5)

                # panel_box.Add(unit_box, flag=wx.EXPAND|wx.ALL, border=5)
                if i % 2 == 0:
                    self.left_box.Add(unit_box, flag=wx.EXPAND|wx.ALL, border=5)
                else:
                    self.right_box.Add(unit_box, flag=wx.EXPAND|wx.ALL, border=5)

            self.Layout()
            self.SetupScrolling(scroll_x = False)

            self.initial_var_count = EnableCount


        # Toggle those enabled and not
        for i in range(0,EnableCount):
            self.name_value[i].Show()
            self.expression_value[i].Show()
            self.equal_bar[i].Show()
            self.enable[i] = True

        for i in range(EnableCount,self.initial_var_count):
            self.name_value[i].Hide()
            self.expression_value[i].Hide()
            self.equal_bar[i].Hide()
            self.enable[i] = False

    def GetValue(self):
        names = [x.Value for x in self.name_value]
        expressions = [x.Value for x in self.expression_value]

        return names, expressions
