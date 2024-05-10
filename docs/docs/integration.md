This library was initially designed to support the Pixoo64 device. However early on the development I realized that the library could be easily extended to support other devices, so I decided to make it as flexible as possible. Now the library is designed to be renderer agnostic, meaning that you can create your own renderer and use the library with any device (physical or virtual) you want. This is mainly done by extending the `Renderer` class and implementing the methods that are needed for the device to work.

## The `Renderer` class

The `Renderer` class is the base class for any renderer that you want to implement. It has a set of attributes and methods that are needed for the library to work, and some of them are mandatory.

### Attributes

!!! info "All the required attributes are marked with an exclamation icon."

- `_size` :fontawesome-solid-circle-exclamation: : The size of the device in pixels.
- `_max_frames`:fontawesome-solid-circle-exclamation: : The maximum number of frames that the device can handle.
- `_pizzoo` :fontawesome-solid-circle-exclamation: : The instance of the `Pizzoo` class that is using the renderer. It is used to access the methods of the `Pizzoo` class.
- `_debug`: The debug mode of the renderer. If set to `True`, the renderer may print debug information on the console.
- `_address`: The address of the device. This is mainly used if your device needs to connect to any IP or physical address.

Any other attribute that you want/need to add to make your renderer work is up to you.

### Methods

!!! info "All the methods that throw a `NotImplementedError` if not implemented are marked with an exclamation icon."

- `__init__`: The initialization method of the renderer. Here you may call the `super().__init__()` method and initialize your own renderer with the needed attributes and setup.
- `get_size`: This method returns `_size` by default, can be overriden to return a different size or to calculate it.
- `get_max_frames`: This method returns `_max_frames` by default, can be overriden to return a different number of frames or to calculate it.
- `get_settings` :fontawesome-solid-circle-exclamation: : This method should return a dictionary with the settings of the renderer. By default it throws a `NotImplementedError`, as this is dependent on the renderer.
- `set_brightness` :fontawesome-solid-circle-exclamation: : This method should set the brightness of the renderer. By default it throws a `NotImplementedError`, as this is dependent on the renderer.
- `switch_frame` :fontawesome-solid-circle-exclamation: : This method should switch on/off the renderer. By default it throws a `NotImplementedError`, as this is dependent on the renderer.
- `render` :fontawesome-solid-circle-exclamation: : This method should render the full animation buffer on the renderer. By default it throws a `NotImplementedError`, and is the main method that you need to implement, as this determines how the renderer will show the animation.
- `compile_node`, `compile_node_root_options` and `render_template_items`: These methods are related to template compilation and are not required at all for integrating a renderer, but if you want to extend your own nodes or options, you may need to implement them. I show you how in the next optional section.

## Extending template rendering capabilities

The library has a built-in compiler that supports an XML/HTML-like language for template processing. This facilitates the design of UIs with relative positioning, defined areas, and reusable components, helping you create fast and reusable interfaces.

This compiler is generic, as it transforms the nodes in drawing methods that are then drawn into a frame (Right now template rendering only works for static images, not animations, so only on one frame). However, you can extend the compiler to support your own nodes and options, so you can react to your own custom nodes, and these nodes will be simply ignored by any other renderer that has no support.

### Processing root node attributes

At the top of any renderer class, you can implement the `compile_node_root_options` method. This method is called when the root node (`<pizzoo>`) is processed, and it receives an `options` dictionary with some root attributes. This method should return a list with tuples `(function, {args})` that will be executed on the render phase. Additionally any other side-effect or action can be done here.

The `options` dictionary has the following keys:

- `brigthness`: The brightness of the renderer.
- `turn_screen`: If the screen should be turned on for starting the render.
- `notification`: If the renderer should trigger a notification system (Sound or similar).
- `clear`: If the renderer should clear the screen before rendering.

!!! example "Current Pixoo64 renderer implementation"
	```python
	def compile_node_root_options(self, options):
		result = []
		if options['brigthness'] is not None:
			result.append((self.set_brightness, {'brightness': options['brigthness']}))
		if options['turn_screen'] is True:
			result.append((self.switch, {}))
		if options['notification'] is True:
			result.append((self.buzzer, {'duration': 2}))
		return result
	```

### Implementing a custom node

Let's see as an example how the `date` node is implemented in the included `ImageRenderer`. This node is there to emulate the network updated `date` command of the `Pixoo64Renderer`, that it's not available on the `ImageRenderer` as this is a static image renderer.

First a new case should be added to the `compile_node` method (That you must implement) of your `Renderer` class.

!!! example "Compiling a `<date>` node on your renderer"
	```python
	def compile_node(self, node, parent, inherited_props, node_props):
		tag = node.tag
		attributes = {}
		abs_x, abs_y = node_props['abs_coords']
		if tag == 'date':
			attributes['color'] = get_color_rgb(node.attrib.get('color', '7'))
			date_format = node.attrib.get('format', 'DD/MM/YYYY')
			# This is a simple way to convert the Pixoo64 format to a python datetime format
			date_format = date_format.replace('DD', '%d').replace('MM', '%m').replace('YYYY', '%Y').replace('WWW', '%a') 
			text = datetime.now().strftime(date_format)
			return (self._pizzoo.draw_text, {'text': text, 'xy': (abs_x, abs_y), **attributes})
	```

The `compile_node` method receives the node, the parent node, the inherited properties, and the node properties. The node is a `lxml` node, so you can access the tag and the attributes of the node. In this case, we are checking if the tag is `date`, and if it is, we are getting the color and the format of the date. Then we are converting the format to a python datetime format and getting the current date in that format. Finally, we are returning a tuple with the drawing method and the attributes that will be used to draw the text.

In case that you don't return a function on the first member of the tuple, the compiler will include the item on a list that will be returned to the renderer after the render phase has finished (Through the `render_template_items` method), so you can decide the logic there.

## Custom existing renderers

Aside from the discussed `Pixoo64Renderer`, there are two other simple renderers included:

- `ImageRenderer`: This renderer is a static image renderer that can be used to test the library without any physical device. It will render the full animation buffer on a single frame and show it on a window.
```python
from pizzoo import ImageRenderer, Pizzoo

pizzoo = Pizzoo('', render=ImageRenderer) #Address is not needed
```

- `WindowRenderer`: A simple and basic renderer that will render the full animation buffer on a single frame and show it on a window. This renderer is used to test the library without any physical device, and on the current iteration lacks a lot of features and functionality.
```python
from pizzoo import WindowRenderer, Pizzoo

pizzoo = Pizzoo('', render=WindowRenderer) #Address is not needed
```

You can use these renderers as a base to create your own renderer, or you can create a new renderer from scratch.

## Submiting a renderer

If you have created a new renderer that you think could be useful for the community, you can submit it to the library. To do so, you can create a pull request on the [GitHub repository](https://github.com/pabletos/pizzoo) and I will review it. If the renderer is useful and well implemented, I will include it in the library and give you credit for it.