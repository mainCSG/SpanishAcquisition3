#######
Changes
#######
* 2022-12-14: **3.0.0**
        Stephen Harrigan

* Updated to work in Python 3.

* 2019-08-09: **2.0.4**
        Zachary Parrott

* Added ability to use a CSV file to generate values for output variables. 
* Additional program in \examples for setting up a virtual sweep titled 'Virtual Setup'


* 2015-04-13: **2.0.2b**
        Kaveh Gharavi (kayghar@gmail.com)

* Memory issues bugging plotting of large data files sloved; merge into second branch *
* Enhancements made by Kyle brought into second branch (version-merge-remote).


* 2014-04-10: **2.0.1a**

  Kaveh Gharavi is now the maintainer
  email: kayghar@gmail.com

  Enhancements:

  *  Added Implementation for Agilent 8753ET transmission/reflection network analyzer
  *  Added Implementation for Stanford Research Systems SR830 digital lock-in amplifier
  *  Added menu feature 'Math->Function' to Data Explorer



* 2012-12-17: **2.0.0a1**

  Enhancements:

  * Added Cryomagnetics Model 4G power supply.
  * Added condition variables throughout the code.
  * Added dynamic quantity wrappers.
  * Made measurement windows default to having "Capture" checked.
  * Y-axis of measurement plots displays units.  Currently just given in terms of fundamental SI units.
  * Make title of Acquisition reflect version number.

  Fixes:

  * If the units of a resource are changed, the GUI display units of the resource will now change too.
  * Fix runscripts script so that it can run files that have been made executable by Git.

  To be completed for 2.0.0:

  * Test the GUI for model4g (see TODOS).
  * Use runtests script with device as opposed to just the mock device.
  * Check rounding on Amps for the model 4g, and make changes in code for this (see TODOs).
  * Test the *rst command with the model 4g (see TODO in source code).

* 2012-09-19: **1.3.0**

  Enhancements:
  
  * Added Lakeshore TC335 device.

* 2012-08-15: **1.2.0**

  Enhancements:
  
  * Added agilent dm34401a multimeter device.

* 2012-07-30: **1.1.0**

  Enhancements:
  
  * Added implementation for older (6 channel) voltage source and Keithley voltage source.
  * Added derivative functionality to data_explorer app
  
  Fixes:
  
  * Fixed a mismatch between data_explorer and installed python scripts

* 2011-10-18: **1.0.3**

  Fixes:

  * Prevented pubsub messages from being parsed in the wrong thread
  * Sped up interface when using variables with units

* 2011-08-25: **1.0.2**

  Fixes:

  * Removed race condition in GUI
  * Minor documentation updates

* 2011-08-23: **1.0.1**

  Enhancements:

  * Changed DPO7104 to use "fastframe" averaging

  Fixes:

  * Minor documentation updates

* 2011-08-22: **1.0.0**

  The initial release.
