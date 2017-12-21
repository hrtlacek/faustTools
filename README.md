# Tools for analyzing Faust programs
At the moment there is one tool present, faustwatch.py

## usage
```usage: faustwatch.py [-h] [--svg] [--ir] [--af AF] [--impLen IMPLEN] [--line]
                     N

Watch a dsp file for changes and take a specific action.

positional arguments:
  N                Path to a .dsp file

optional arguments:
  -h, --help       show this help message and exit
  --svg            Make an svg block diagram and open it.
  --ir             Get impulse response and plot it.
  --af AF          Send through audio file.
  --impLen IMPLEN  Length of impulse. Default is unit impulse, so 1.
  --line           Get response to line from -1 to 1. So input-output
                   amplitude relationship.
```