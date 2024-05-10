# Installation

## Requirements

- Python 3.6 or higher
- Pip
- A working pixoo64 device (Future support for other devices will be hopefully added)

## Package installation

To install the package, run the following command:
```bash
pip install pizzoo
```
Everything should be installed correctly if you don't see any errors.

## Connect with the device

This section assumes that you are using the library to connect to a [Pixoo64 device](https://divoom.com/es/products/pixoo-64), if you want to use the library for rendering on another device or simply use a different renderer, just [check this section instead](integration.md).

!!! note

	Network scanning for automatic Pixoo64 connection is an already planned feature, however, this seems like a relatively big feature for so little gain, so it's not something planned until some other fixes and improvements are done.

### Get your device IP
Currently the Pixoo64 renderer has no auto-find feature enabled, so you have to get your device IP first, for doing so:

1. Open your Divoom app on your phone.
2. Go to the first section, the one related to your device.
3. Click on your device name.
4. In the next screen the local IP should be shown on the bottom right side. That's the one needed.

### Initialize your Pizzoo instance
For creating and initializing your Pizzoo instance you only need to be connected to the same local network and initialize it this way:
```python
from pizzoo import Pizzoo

pizzoo = Pizzoo('192.168.xx.xxx', debug=True)
```
Where `192.168.xx.xxx` is the local IP of your Pixoo64 device.

Now you are ready to start playing with it!

### Simple connection test
If the connection fails, an error should be trown, but if that doesn't happen and you're not sure if it's working, you can then do:
```python
pizzoo.buzzer(1, 1, 4)
```
This will make the pizzoo beep two times.
