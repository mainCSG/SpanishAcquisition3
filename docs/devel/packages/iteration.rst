#########
Iteration
#########

Tools for iterating; the core of the logic behind sweeping.

File structure
**************

The package consists of only two modules: :mod:`spacq.iteration.sweep` which contains :class:`~spacq.iteration.sweep.SweepController`, and :mod:`spacq.iteration.variables` which defines input, condition and output variables. Together, these modules can be used to provide iteration over a set of variables.

Sweeping
********

:class:`spacq.iteration.sweep.SweepController` goes through a process of several stages, as crudely drawn in its docstring::

							   conditional_dwell
				                              v       ^
   init -> next -> transition -> write -> dwell -> pulse -> read -> condition -> ramp_down -> end
   ^       ^                                  |_____________^           |             |
   |       |____________________________________________________________|             |
   |__________________________________________________________________________________|	

The ordering is approximately linear, but with some loops and skips:

* If no pulse program is defined, the ``pulse`` stage is skipped.
* If at least one of the changed order's condition variables evaluate to false, ``condition`` heads to ``conditional_dwell``.  Otherwise, if more items remain to be iterated over, ``condition`` heads to ``next``.
* If the sweep is continuous, ``ramp_down`` restarts it instead of finishing it.

Those steps which deal with accessing resources (``transition``, ``write``, ``read``, ``ramp_down``) do so in parallel, using as many concurrent :class:`threading.Thread` objects as necessary.

The sweeping process can be interrupted at any time for many reasons; some of these include: user error, device error, and the user pressing the "Cancel" button. In the case that it is interrupted, the sweep simply proceeds to either the ``ramp_down`` or the ``end`` stage, depending on whether the interruption is fatal. In the case of a fatal interruption, the ``ramp_down`` stage cannot be expected to succeed (for example, if writing to a resource failed), so it is skipped.
