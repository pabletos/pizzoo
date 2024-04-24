import base64
import json
from enum import IntEnum
from math import floor

from requests import post
from PIL import Image, ImageOps

from math import floor
from time import time, sleep
from xml.etree.ElementTree import ElementTree, fromstring
from ._constants import PICO_PALETTE, DIAL_DEFAULT_ITEM, PICO_HEX_PALETTE
from ._utils import clamp
from ._renderers import Pixoo64Renderer, Renderer, ImageRenderer, WindowRenderer
from os.path import dirname, realpath, join


class Pizzoo:
	__buffer = []
	__current_frame = -1
	__max_frames = 60
	__debug = False
	__fonts = {}
	__current_dir = dirname(realpath(__file__))

	def __init__(self, address, renderer=Pixoo64Renderer, renderer_params={}, debug=False):
		self.renderer = renderer(address=address, debug=debug, **renderer_params)
		self.__compute_device_specs()
		self.__debug = debug
		# Initialize buffer
		self.add_frame()
		# get current dir of this file:
		self.load_font('default', join(self.__current_dir, 'MatrixLight6.bdf'), False)

	def __compute_device_specs(self):
		self.size = self.renderer.get_size()
		self.pixel_count = self.size * self.size
		self.__max_frames = self.renderer.get_max_frames()
		
	def load_font(self, font_name, path, soft=True):
		'''
		Loads a new font on bdf format to be used on the draw_text method.

		Parameters:
		- font_name (str): The name to identify the font.
		- path (str): The path to the font file.
		- soft (bool): If True, the font will be loaded when used. If False, the font will be loaded now.
		
		Returns:
		- None
		'''
		if soft:
			self.__fonts[font_name] = path
		else:
			from bdfparser import Font
			self.__fonts[font_name] = Font(path)

	def load_fonts(self, fonts):
		'''
		Loads multiple fonts at once.

		Parameters:
		- fonts (dict): A dictionary with the font name as key and the font path as value.

		Returns:
		- None
		'''
		for font_name, path in fonts.items():
			self.load_font(font_name, path)
		
	def cls(self, rgb=(0, 0, 0)):
		'''
		Clears the current frame with the given color.

		Parameters:
		- rgb (tuple(int, int, int) | int | string): The color to clear the frame with. Default is black.
		
		Returns:
		- None
		'''
		rgb = self.__get_color_rgb(rgb)
		self.__buffer[self.__current_frame] = [rgb[0], rgb[1], rgb[2]] * self.pixel_count

	def add_frame(self, rgb=(0, 0, 0)):
		'''
		Adds a new frame to the animation buffer.

		Parameters:
		- rgb (tuple(int, int, int) | int | string): The color to fill the frame with. Default is black.
		
		Returns:
		- None
		'''
		assert self.__current_frame <= self.__max_frames, f'Frame limit reached, push before reaching {self.__max_frames} frames'
		frame = []
		for _ in range(self.pixel_count):
			frame.extend(rgb)
		self.__buffer.append(frame)
		self.__current_frame = len(self.__buffer) - 1

	def reset_buffer(self):
		'''
		Resets the animation buffer, removing all frames and adding a new one.
		'''
		self.__buffer = []
		self.__current_frame = -1
		self.add_frame()

	def draw_pixel(self, xy, color):
		'''
		Draws a single pixel on the current frame at the given coordinates.

		Parameters:
		- xy (tuple(int, int)): The coordinates to draw the pixel at.
		- color (tuple(int, int, int) | int | string): The color to draw the pixel with.

		Raises:
		- ValueError: If the given coordinates are out of bounds.

		Returns:
		- None
		'''
		index = xy[0] + (xy[1] * self.size)
		rgb = self.__get_color_rgb(color)
		if index < 0 or index >= self.pixel_count:
			raise ValueError(f'Invalid index given: {index} (maximum index is {self.pixel_count - 1})')
		# FIXME: Could we maybe move to rgba and use the alpha channel to determine if the pixel is on or off? -> index = index * 4
		index = index * 3
		self.__buffer[self.__current_frame][index + 1] = rgb[1]
		self.__buffer[self.__current_frame][index] = rgb[0]
		self.__buffer[self.__current_frame][index + 2] = rgb[2]

	def draw_rectangle(self, xy, width, height, color, filled=True):
		'''
		Draws a rectangle on the current frame at the given coordinates.

		Parameters:
		- xy (tuple(int, int)): The coordinates of the top-left corner of the rectangle.
		- width (int): The width of the rectangle.
		- height (int): The height of the rectangle.
		- color (tuple(int, int, int) | int | string): The color to draw the rectangle with.
		- filled (bool): Whether to fill the rectangle or not.

		Returns:
		- None
		'''
		for x in range(xy[0], xy[0] + width):
			for y in range(xy[1], xy[1] + height):
				if filled or x == xy[0] or x == xy[0] + width - 1 or y == xy[1] or y == xy[1] + height - 1:
					self.draw_pixel((x, y), color)

	def draw_circle(self, xy, radius, color, filled=True):
		'''
		Draws a circle on the current frame at the given coordinates.

		Parameters:
		- xy (tuple(int, int)): The coordinates of the center of the circle.
		- radius (int): The radius of the circle.
		- color (tuple(int, int, int) | int | string): The color to draw the circle with.
		- filled (bool): Whether to fill the circle or not.

		Returns:
		- None
		'''
		for x in range(xy[0] - radius, xy[0] + radius + 1):
			for y in range(xy[1] - radius, xy[1] + radius + 1):
				if (x - xy[0]) ** 2 + (y - xy[1]) ** 2 <= radius ** 2:
					self.draw_pixel((x, y), color)
	
	def draw_image(self, image_or_path, xy=(0, 0), size='auto', resample_method=Image.NEAREST):
		'''
		Draws an image on the current frame at the given coordinates.

		Parameters:
		- image_or_path (str | Image): The path to the image file or the Image object to draw.
		- xy (tuple(int, int)): The coordinates of the top-left corner of the image.
		- size (tuple(int, int) | str): The size to resize the image to. If 'auto' is given, the image will be resized to fit the screen if needed.
		- resample_method (Resampling): The resample mode to use when resizing the image to fit the screen. Default is Image.NEAREST.
		
		Returns:
		- None
		'''
		if isinstance(image_or_path, str):
			image = Image.open(image_or_path)
		else:
			image = image_or_path
		width, height = self.__compute_image_resize(image, size)
		image = ImageOps.fit(image, (width, height), method=resample_method, centering=(0.5, 0.5))
		image = image.convert('RGBA')
		for x in range(image.width):
			for y in range(image.height):
				rgba = image.getpixel((x, y))
				if rgba[3] > 0:
					placed_x, placed_y = x + xy[0], y + xy[1]
					if self.size - 1 < placed_x or placed_x < 0 or self.size - 1 < placed_y or placed_y < 0:
						continue
					self.draw_pixel((placed_x, placed_y), rgba)

	def draw_gif(self, gif_path, xy=(0, 0), size='auto', loop=False, resample_method=Image.NEAREST, fill='auto'):
		'''
		Draws a gif on the animation buffer, starting on current frame. If the gif is larger than the screen, it will be resized to fit the screen.
		
		Parameters:
		- gif_path (str): The path to the gif file.
		- xy (tuple(int, int)): The coordinates to start drawing the gif at.
		- size (tuple(int, int) | str): The size to resize the gif to. If 'auto' is given, width and height of the gif will be used and resized if needed to fit the screen.
		- loop (bool): Whether to loop the gif or not.
		- resample_method (Resampling): The resample mode to use when resizing the gif to fit the screen. Default is Image.NEAREST.
		- fill (tuple(int, int, int) | str): The color to fill the screen with before drawing the gif. If 'auto' is given, the color will be black.

		Returns:
		- None
		'''
		current_frame = self.__current_frame if self.__current_frame >= 0 else 0
		gif = Image.open(gif_path)
		remaining_frames = self.__max_frames - current_frame
		total_frames = remaining_frames if loop else min(remaining_frames, gif.n_frames)
		current_gif_frame = 0
		for frame in range(0, total_frames):
			if frame >= self.__max_frames:
				break
			try:
				current_gif_frame += 1
				gif.seek(current_gif_frame)
			except EOFError:
				current_gif_frame = 0
				gif.seek(current_gif_frame)
			if fill == 'auto':
				self.cls()
			elif fill is not None:
				self.cls(fill)
			self.draw_image(gif, xy, size, resample_method)
			if frame < total_frames - 1:
				if len(self.__buffer) < self.__current_frame + 2:
					self.add_frame()
				else:
					self.__current_frame += 1
		self.__current_frame = current_frame

	def __get_font(self, font_name):
		if font_name not in self.__fonts:
			raise ValueError(f'Font "{font_name}" not found')
		if type(self.__fonts[font_name]) == str:
			from bdfparser import Font
			self.__fonts[font_name] = Font(self.__fonts[font_name])
		return self.__fonts[font_name]

	def draw_text(self, text, xy=(0, 0), font='default', color='#FFFFFF', align=0, line_width='auto'):
		'''
		Draws a text on the current frame at the given coordinates.

		Parameters:
		- text (str): The text to draw.
		- xy (tuple(int, int)): The coordinates of the top-left corner of the text.
		- font (str): The name of the font to use. Default is 'default'.
		- color (tuple(int, int, int) | int | string): The color to draw the text with.
		- align (int): The alignment of the text. 0 is left, 1 is center and 2 is right.
		- line_width (int): The maximum width of the text. Default is 'auto'.

		Returns:
		- None
		'''
		line_width = self.size if line_width == 'auto' else line_width
		font = self.__get_font(font)
		rgb = self.__get_color_rgb(color)
		bitmap = font.draw(text, missing='?', linelimit=line_width)
		text_data = bitmap.todata(2)
		width, height = bitmap.width(), bitmap.height()
		for x in range(width):
			for y in range(height):
				if text_data[y][x]:
					placed_x, placed_y = x + xy[0], y + xy[1]
					if self.size - 1 < placed_x or placed_x < 0 or self.size - 1 < placed_y or placed_y < 0:
						continue
					self.draw_pixel((placed_x, placed_y), rgb)

	def __compute_image_resize(self, image, size):
		if size == 'auto':
			width = image.width
			height = image.height
			if width > self.size:
				height = floor(height * self.size / width)
				width = self.size
			elif height > self.size:
				width = floor(width * self.size / height)
				height = self.size
		elif size == 'fill-width':
			width = self.size
			height = floor(image.height * self.size / image.width)
		elif size == 'fill-height':
			width = floor(image.width * self.size / image.height)
			height = self.size
		elif isinstance(size, tuple):
			width, height = size
		else:
			raise ValueError('Invalid size value')
		return width, height

	def draw_line(self, start, end, color):
		'''
		Draws a line on the current frame from the start to the end coordinates.

		Parameters:
		- start (tuple(int, int)): The coordinates of the start of the line.
		- end (tuple(int, int)): The coordinates of the end of the line.
		- color (tuple(int, int, int) | int | string): The color to draw the line with.

		Returns:
		- None
		'''
		x0, y0 = start
		x1, y1 = end
		dx = abs(x1 - x0)
		dy = abs(y1 - y0)
		sx = 1 if x0 < x1 else -1
		sy = 1 if y0 < y1 else -1
		err = dx - dy
		while x0 != x1 or y0 != y1:
			self.draw_pixel((x0, y0), color)
			e2 = 2 * err
			if e2 > -dy:
				err -= dy
				x0 += sx
			if e2 < dx:
				err += dx
				y0 += sy

	def render(self, frame_speed=150):
		'''
		Renders the current animation buffer to the Pixoo device. After that it resets the buffer.
		Take into account that only a max of 60 frames can be rendered at once. So any buffer with more than 60 frames will be truncated.

		Parameters:
		- frame_speed (int): The speed in milliseconds per frame. Default is 150. (Only useful if more than 1 frame is being rendered)
		
		Returns:
		- None
		'''
		self.renderer.render(self.__buffer, frame_speed)
		self.reset_buffer()

	def set_dial(self, items, background=None, clear=True):
		'''
		Sets the dial on the device with the given items. These are networking commands on the pixoo device that manage things like temperature, weather, time, etc.
		Most of them just auto-update, so it's useful for creating custom dials (Like watchfaces, for example).
		
		Parameters:
		- items (list(dict)): A list of items to display on the dial. Each item should have at least a 'DisplayType' type.
		- background (str): The path to an image to use as the background of the dial. Default is None.
		- clear (bool): Whether to send a network clear for the current text on the device or not. Default is True.

		Returns:
		- None

		Note: This method is pretty raw and depends on knowing the exact parameters to send to the device. It's recommended to use the higher-level render_template method.
		If needed additional documentation can be found on the official API (https://doc.divoom-gz.com/web/#/12?page_id=234).
		'''
		if background is not None:
			path_ext = background.split('.')[-1]
			if path_ext == 'gif':
				self.draw_gif(background, size='auto', fill='auto')
			else:
				self.draw_image(background)
			self.render()
		if clear:
			self.clear_remote_text()
		processed_items = [{'TextId': index + 1, **DIAL_DEFAULT_ITEM, **item} for index, item in enumerate(items)]
		self.__request('Draw/SendHttpItemList', {
			'ItemList': processed_items
		})
	
	def switch(self, on=True):
		'''
		Turns the device on or off.
		'''
		self.renderer.switch(on)
	
	def get_settings(self):
		'''
		Get the current settings from the device.

		Returns:
		- dict: The current settings of the device.
		'''
		return self.renderer.get_settings()
	
	def set_brightness(self, brightness):
		'''
		Sets the brightness of the device.

		Parameters:
		- brightness (int): The brightness value to set. Must be between 0 and 100.

		Returns:
		- None
		'''
		self.renderer.set_brightness(brightness)
	
	def __node_position(self, x, y, position, prev_x, prev_y, rel_x, rel_y):
		'''
			- static: x and y are relative to last non-absolute parent
			- relative: as static, but absolute children are relative to this element
			- absolute: x and y are absolute to the last relative element or the screen
		'''
		abs_x = x
		abs_y = y
		position_props = {}  
		if position == 'absolute':
			abs_x = abs_x + rel_x
			abs_y = abs_y + rel_y
		else:
			abs_x = prev_x + abs_x
			abs_y = prev_y + abs_y
			position_props['x'] = abs_x
			position_props['y'] = abs_y
			if position == 'relative': 
				position_props['rel_x'] = abs_x
				position_props['rel_y'] = abs_y
		return abs_x, abs_y, position_props
	
	def __node_size(self, node, x, y, abs_x, abs_y, ancestor_props):      
		container_width = ancestor_props.get('width', self.size)
		container_height = ancestor_props.get('height', self.size)
		width = node.attrib.get('width', '100%')
		height = node.attrib.get('height', '100%')
		width = int(width[:-1]) * container_width // 100 if width[-1] == '%' else int(width)
		height = int(height[:-1]) * container_height // 100 if height[-1] == '%' else int(height)
		width = clamp(width, 1, container_width - x)
		height = clamp(height, 1, container_height - y)
		return width, height
	
	def __node_coords(self, node, ancestor_props):
		x = node.attrib.get('x', '0')
		y = node.attrib.get('y', '0')
		x = int(x[:-1]) * ancestor_props.get('width', self.size) // 100 if x[-1] == '%' else int(x)
		y = int(y[:-1]) * ancestor_props.get('height', self.size) // 100 if y[-1] == '%' else int(y)
		return x, y
	
	def __command_atributes(self, node):
		attributes = {}
		attributes['dir'] = node.attrib.get('scroll', 'left')
		attributes['dir'] = 0 if attributes['dir'] == 'left' else 1
		try:
			attributes['font'] = int(node.attrib.get('font', '2'))
		except:
			attributes['font'] = 18 if node.attrib['font'] == 'small' else 2
		attributes['speed'] = clamp(int(node.attrib.get('speed', '100')), 1, 100)
		attributes['color'] = node.attrib.get('color', '7')
		try:
			attributes['color'] = PICO_HEX_PALETTE[int(attributes['color'])]
		except:
			attributes['color'] = attributes['color']
		attributes['align'] = node.attrib.get('align', 'left')
		attributes['align'] = 1 if attributes['align'] == 'left' else 2 if attributes['align'] == 'center' else 3
		if 'update' in node.attrib:
			attributes['update_time'] = int(node.attrib['update'])
		return attributes
	
	def __get_node_color(self, color_str):
		if color_str.isdigit():
			return int(color_str)
		if color_str[0] == '#':
			return tuple(int(color_str[i:i+2], 16) for i in (1, 3, 5))
		if color_str[0] == '(' and color_str[-1] == ')':
			return tuple(int(x) for x in color_str[1:-1].split(','))
		return color_str

	def __compile_node(self, node, parent_node=None, inherited_props=None):
		tag = node.tag
		new_props = inherited_props.copy() if inherited_props is not None else {}
		result = None
		abs_x, abs_y = 0, 0
		x, y = self.__node_coords(node, new_props)
		position_props = {}
		# Now this computation is used for every node
		abs_x, abs_y, position_props = self.__node_position(
			x,
			y,
			node.attrib.get('position', 'static'),
			new_props.get('x', 0),
			new_props.get('y', 0),
			new_props.get('rel_x', 0),
			new_props.get('rel_y', 0)
		)
		if tag == 'section':
			width, height = self.__node_size(node, x, y, abs_x, abs_y, new_props)
			new_props['width'] = width
			new_props['height'] = height
			result = None
		elif tag == 'line':
			x2 = int(node.attrib.get('x2', '0'))
			y2 = int(node.attrib.get('y2', '0'))
			abs_x2, abs_y2, _ = self.__node_position(
				x2,
				y2,
				node.attrib.get('position', 'static'),
				new_props.get('x', 0),
				new_props.get('y', 0),
				new_props.get('rel_x', 0),
				new_props.get('rel_y', 0)
			)
			color = self.__get_node_color(node.attrib.get('color', '7'))
			result = (self.draw_line, {'start': (abs_x, abs_y), 'end': (abs_x2, abs_y2), 'color': color})
		elif tag == 'rectangle':
			# end position compute
			color = self.__get_node_color(node.attrib.get('color', '7'))
			width, height = self.__node_size(node, x, y, abs_x, abs_y, new_props)
			new_props['width'] = width
			new_props['height'] = height
			result = (self.draw_rectangle, {'xy': (abs_x, abs_y), 'width': width, 'height': height, 'color': color, 'filled': True})
		elif tag == 'circle':
			color = self.__get_node_color(node.attrib.get('color', '7'))
			radius = int(node.attrib.get('radius', '8'))
			result = (self.draw_circle, {'xy': (abs_x, abs_y), 'radius': radius, 'color': color})
		elif tag == 'text':
			color = self.__get_node_color(node.attrib.get('color', '7'))
			shadow = node.attrib.get('shadow', None)
			shadow_color = eval(node.attrib.get('shadow_color', '0'))
			font = node.attrib.get('font', 'default')
			text = node.text
			wrap = node.attrib.get('wrap', 'false').lower() == 'true'
			line_width = 'auto'
			if wrap:
				width, height = self.__node_size(node, x, y, abs_x, abs_y, new_props)
				line_width = width
			if text is None:
				text = ''
			result = (self.draw_text, {'text': text, 'xy': (abs_x, abs_y), 'color': color, 'font': font, 'line_width': line_width})
		elif tag == 'pixel':
			color = self.__get_node_color(node.attrib.get('color', '7'))
			result = (self.draw_pixel, {'xy': (abs_x, abs_y), 'rgb': color})
		elif tag == 'image':
			path = node.attrib.get('src', None)
			# add size
			result = (self.draw_image, {'image_or_path': path, 'xy': (abs_x, abs_y)})
		'''
		elif tag == 'message':
			text = node.text
			width, height = self.__node_size(node, x, y, abs_x, abs_y, new_props)
			attributes = self.__command_atributes(node)
			result = (DisplayType.TEXT_MESSAGE, {**attributes, 'TextString': text, 'x': abs_x, 'y': abs_y, 'TextWidth': width, 'TextHeight': height})
		elif tag == 'time':
			attributes = self.__command_atributes(node)
			width, height = self.__node_size(node, x, y, abs_x, abs_y, new_props)
			time_format = node.attrib.get('format', 'HH:mm:ss')
			if time_format == 'HH:mm:ss':
				dt = DisplayType.HOUR_MIN_SEC
			elif time_format == 'HH':
				dt = DisplayType.HOUR
			elif time_format == 'HH:mm':
				dt = DisplayType.HOUR_MIN
			elif time_format == 'mm':
				dt = DisplayType.MINUTE
			elif time_format == 'ss':
				dt = DisplayType.SECOND
			result = (dt, {**attributes, 'x': abs_x, 'y': abs_y, 'TextWidth': width, 'TextHeight': height})
		elif tag == 'temperature':
			attributes = self.__command_atributes(node)
			width, height = self.__node_size(node, x, y, abs_x, abs_y, new_props)
			temp_format = node.attrib.get('kind', 'actual')
			if temp_format == 'actual':
				dt = DisplayType.TEMP_DIGIT
			elif temp_format == 'max':
				dt = DisplayType.TODAY_MAX_TEMP
			elif temp_format == 'min':
				dt = DisplayType.TODAY_MIN_TEMP
			result = (dt, {**attributes, 'x': abs_x, 'y': abs_y, 'TextWidth': width, 'TextHeight': height})     
		elif tag == 'weather':
			attributes = self.__command_atributes(node)
			width, height = self.__node_size(node, x, y, abs_x, abs_y, new_props)
			result = (DisplayType.WEATHER_WORD, {**attributes, 'x': abs_x, 'y': abs_y, 'TextWidth': width, 'TextHeight': height})
		elif tag == 'date':
			attributes = self.__command_atributes(node)
			width, height = self.__node_size(node, x, y, abs_x, abs_y, new_props)
			date_format = node.attrib.get('format', 'DD/MM/YYYY')
			if date_format == 'DD/MM/YYYY':
				dt = DisplayType.DAY_MONTH_YEAR
			elif date_format == 'DD':
				dt = DisplayType.DAY
			elif date_format == 'MM':
				dt = DisplayType.MONTH
			elif date_format == 'MMM':
				dt = DisplayType.ENG_MONTH
			elif date_format == 'YYYY':
				dt = DisplayType.YEAR
			elif date_format == 'MM/YY':
				dt = DisplayType.MONTH_YEAR
			elif date_format == 'WW':
				dt = DisplayType.ENG_WEEK_TWO
			elif date_format == 'WWW':
				dt = DisplayType.ENG_WEEK_THREE
			elif date_format == 'WWWW':
				dt = DisplayType.ENG_WEEK_FULL
			result = (dt, {**attributes, 'x': abs_x, 'y': abs_y, 'TextWidth': width, 'TextHeight': height})
		'''
		new_props = {**new_props, **position_props}
		return result, new_props
	
	def __get_root_options(self, root):
		options = []
		attribs = root.attrib
		brigthness = attribs.get('brightness', None)
		turn_screen = bool(attribs.get('turnOn', False))
		clear = bool(attribs.get('clear', False))
		notification = bool(attribs.get('notification', False))
		'''
		if brigthness is not None:
			options.append((self.set_brightness, {'brightness': clamp(int(brigthness), 0, 100)}))
		if turn_screen is True:
			options.append((self.set_screen_on, {}))
		if clear is True:
			options.append((self.clear, {}))
		if notification is True:
			options.append((self.buzzer, {'duration': 2}))
		'''
		return options
	
	def __compile_template(self, template):
		tree = ElementTree(fromstring(template))
		root = tree.getroot()
		assert root.tag == 'pizzoo', 'Root tag must be "pizzoo"'
		commands = self.__get_root_options(root)
		pending = [{'node': tree.getroot(), 'parent': None, 'props': {}}]
		while len(pending) > 0:
			current = pending.pop(0)
			command, props = self.__compile_node(current['node'], current['parent'], current['props'] )
			if command is not None:
				commands.append(command)
			for child in current['node']:
				pending.append({'node': child, 'parent': current, 'props': props})
		return commands

	# https://stackoverflow.com/questions/61834266/super-fast-way-to-compare-if-two-strings-are-equal
	def render_template(self, template, use_cache=True):
		self.cls()
		commands = self.__compile_template(template)
		dial_items = []
		for command in commands:
			'''
			if type(command[0]) is DisplayType:
				dial_items.append({'type': command[0], **command[1]})
			else:   
				command[0](**command[1])
			'''
			command[0](**command[1])
		self.render()
		'''
		if len(dial_items) > 0:
			# workaround for a desync error with the divoom device when sending dial items
			sleep(0.2)
			self.set_dial(dial_items)
		'''

	def __get_color_rgb(self, color):
		if isinstance(color, tuple):
			return color
		if isinstance(color, int):
			return PICO_PALETTE[color]
		if isinstance(color, str) and color[0] == '#' and len(color) == 7:
			return tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
		raise ValueError('Invalid color format')
	
	def __getattr__(self, name):
		if hasattr(self.renderer, name) and callable(getattr(self.renderer, name)):
			return getattr(self.renderer, name)
		raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")


__all__ = (Pizzoo, Renderer, ImageRenderer, WindowRenderer)