# Tools for analyzing Faust programs
At the moment there is one tool present, faustwatch.py

## Faustwatch

Faustwatch is a tool that observes a .dsp file used by the dsp language [FAUST](https://faust.grame.fr/). If the file is changed (saved after editing), the blockdiagram can be automatically shown in the default browser, the impulse response can be plottet and more.
Basically it is supposed to make FAUST development faster.

Here you can see it in action:
![](demo.gif)

### usage
``` bash
usage: faustwatch [-h] [--svg] [--ir] [--af AF] [--impLen IMPLEN] [--line] N

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
                   amplitude relationship. Useful for plotting transfer
                   functions of non-linearities

```