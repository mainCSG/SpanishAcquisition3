#!/usr/bin/env python2

from spacq.gui.tool.box import Dialog, MessageDialog, save_csv
from spacq.iteration.virtual_variables import virtLinSpaceConfig, DependentConfig, virtSweepController, sort_output_variables
from spacq.gui.config.virtual_variables import MultipleVariableConfigPanel, DependentVariableConfigPanel
from spacq.gui.global_store import GlobalStore
from spacq import VERSION
import numpy
import wx
import logging
logging.basicConfig(level=logging.WARNING)


class VariableSweepFrame(wx.Frame):
    def __init__(self, parent, *args, **kwargs):
        wx.Frame.__init__(self, parent, *args, **kwargs)

        # for evaluation MessageDialog
        self.parent = parent

        # Frame
        frame_box = wx.FlexGridSizer(rows=4, columns=1, vgap=5, hgap=5)

        # top = ButtonPanel(self)
        self.virtual_panel = MultipleVariableConfigPanel(self)
        # self.variables_panel = VariablesPanel(self, global_store)
        # self.variables_panel.SetMinSize((800, 300))

        self.dependent_panel = DependentVariableConfigPanel(self)

        frame_box.Add(self.virtual_panel, 1)  # , wx.EXPAND)
        frame_box.Add(self.dependent_panel, 1, flag=wx.EXPAND |
                      wx.ALIGN_CENTER_VERTICAL)
        # frame_box.Add(self.variables_panel, 1, wx.EXPAND)

        button = wx.Button(self, label='Evaluate / Write CSV')
        frame_box.Add(button, 1, wx.EXPAND)
        self.Bind(wx.EVT_BUTTON, self.OnButton, button)

        self.SetSizerAndFit(frame_box)

    def OnButton(self, evt=None):

        # Retrieve info from virtual variable config
        tempVars = self.virtual_panel.GetValue()
        virtVars = [None]*self.virtual_panel.var_count.Value

        for i in range(0, self.virtual_panel.var_count.Value):
            name = tempVars[0][i]
            initial = tempVars[1][i]
            final = tempVars[2][i]
            steps = tempVars[3][i]
            order = tempVars[4][i]

            virtVars[i] = virtLinSpaceConfig(
                name, initial, final, steps, order)

        variables, num_periods = sort_output_variables(virtVars)

        # Sort by order and write array of virtual variables
        sweepSweep = virtSweepController(variables, num_periods)
        sweepSweep.sweepTable()

        # Get info from dependent variable definitions
        realVarInfo = self.dependent_panel.GetValue()
        realVars = [None]*self.dependent_panel.dependent_count.Value

        for i in range(0, self.dependent_panel.dependent_count.Value):
            name = realVarInfo[0][i]
            expression = realVarInfo[1][i]

            realVars[i] = DependentConfig(name, expression)

        # Evaluate expressions
        RetrieveValues = [var.DependentFunctionMath(
            sweepSweep.names, sweepSweep.value_history) for var in realVars]
        dependentNames = [var.name for var in realVars]

        # Reconfigure shape
        dependentValues = RetrieveValues[0]

        if len(RetrieveValues) == 1:
            # Go from list to numpy column
            dependentValues = numpy.c_[dependentValues]
        else:
            for values in RetrieveValues[1:]:
                dependentValues = numpy.column_stack((dependentValues, values))

        # Prepare headings and virtual and dependent values for csv writing
        PrintNames = sweepSweep.names
        PrintNames.extend(dependentNames)

        outputTable = numpy.append(
            sweepSweep.value_history, dependentValues, axis=1)

        # TODO: need to sort out parent stuff for message dialog
        try:
            result = save_csv(self, outputTable, PrintNames)

        except IOError as e:
            # May need to be self.parent if this error ever gets called
            # TODO: probably doesnt work hard to test
            MessageDialog(self, str(e), 'Could not save data').Show()
            return


class VirtualSetupApp(wx.App):
    def OnInit(self):

        # Frames
        self.exp_frame = VariableSweepFrame(None, title='Virtual Setup')

        # Menu.
        menuBar = wx.MenuBar()

        # Configuration.
        menu = wx.Menu()

        # Help.
        menu = wx.Menu()
        menuBar.Append(menu, '&Help')

        # About.
        item = menu.Append(wx.ID_ABOUT, '&About...')
        self.Bind(wx.EVT_MENU, self.OnMenuHelpAbout, item)

        self.exp_frame.SetMenuBar(menuBar)

        # Display.
        self.exp_frame.SetSizerAndFit(self.exp_frame.Sizer)
        self.exp_frame.Show()
        self.SetTopWindow(self.exp_frame)
        self.exp_frame.Raise()

        self.exp_frame.Show(True)

        return True

    def OnMenuHelpAbout(self, evt=None):
        info = wx.AboutDialogInfo()
        info.SetName('Virtual Setup')
        info.SetDescription(
            'An application for setting up linear sweeps of virtual\n'
            'variables for output variables.\n'
            '\n'
            'Using Spanish Acquisition version {0}.'.format(VERSION)
        )

        wx.AboutBox(info)


if __name__ == "__main__":
    app = VirtualSetupApp()
    app.MainLoop()
