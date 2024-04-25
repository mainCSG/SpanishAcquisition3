######################
Cryomagnetics Model 4G
######################

The implementation for the Cryomagnetics Model 4G power supply is :class:`spacq.devices.cryomagnetics.model4g.Model4G`.

It is assumed the reader has read the manual for the Model 4G.

.. _device_specific_model4g_virtual_resources:

Virtual resources
*****************

Along with all the resources that are mostly direct representations of controls on the power supply's interface, the device class has higher level virtual resources.  These are resources that are constructed from the more direct resources. Following are descriptions of what these new functions do:

* **virt_both_units**: Switches units on both channels simultaneously.  Will read 'unequal' for its output if units on channels are not equal.  Otherwise, reads the current units.
* **virt_both_heaters**: Switches both persistent heater switches simultaneously.  Useful for avoiding eddy currents.
* **virt_iout_sweep_to**: Set a target for the power supply current to sweep to, and start the sweep.
* **virt_imag_sweep_to**: Set a target for the magnet current to sweep to, and start the sweep.
* **virt_sync_currents**: Sweeps the power supply current to the magnet current.  Output will give whether or not currents are synced.
* **virt_iout**: The same as **virt_iout_sweep_to**, but after starting the sweep, Spanish Acquisition will halt until the sweep is complete. In effect, this is a dynamic version of the wait time that output variables can be assigned.  The output gives the power supply current.
* **virt_imag**: Same as **virt_imag**, but for magnet current.  Note that this is also affected by **virt_energysave_mode**.  The output gives the magnet current.
* **virt_energysave_mode**: Supplies a variety of modes to save energy when using **virt_imag**, described in :ref:`energy saving modes <device_specific_model4g_energy_saving_modes>`.
* **virt_heater_wait_mode**: If set to 1, Spanish Acquisition will sleep for a second after a persistent switch heater is toggled.
* **virt_sweep_sleep**: The application halting functionality within **virt_imag** and **virt_iout** will double-check if the sweep is complete.  **virt_sweep_sleep** defines a sleep delay between the first and second check.  This is useful for dealing with the overshoot that may occur in reaching the target with the sweep.  It is possible that the halting functionality will see the sweep as complete when the present current equals the target current just before overshooting.

Note that these virtual resources are not internally independent with respect to the lower level resources.  For example, **virt_iout_sweep_to** and **virt_imag_sweep_to** both will change the power supply current.  This is because, as the manual should make clear, in order to change the magnet current the power supply current is changed while the persistent switch heater is on.

Usage with condition variables
******************************

If using the resources **virt_iout_sweep_to** or **virt_imag_sweep_to**, :ref:`condition variables <general_concepts_condition_variables>` can be used to acquire measurements while the power supply is sweeping.  To do this, make use of the behaviour that occurs when a condition variable is in an order below all the output variables.


.. _device_specific_model4g_energy_saving_modes:

Energy saving modes
*******************

The virtual resource **virt_energysave_mode** has 5 modes, which affect the behaviour of **virt_imag**:

* **0**: Does nothing.  This is the default mode.
* **1**: Both switch heaters will be flipped on, the target to sweep to set, then upon reaching the target, both switch heaters will be turned off.
* **2**: Same as **1**, but only affects the switch heater of the channel being acted upon. Note that this will induce eddy currents.
* **3**: Similar to **1**, but after setting the heater switches off, the power supply current is sweeped to zero.  Also, before flipping the switch heaters on, the currents are synced.
* **4**: Similar to **3**, but only uses the relevant switch heater (the same as how **2** differs from **1**).

