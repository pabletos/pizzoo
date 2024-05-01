from json import dumps
from requests import post
from base64 import b64encode
from math import floor
from ._utils import clamp, get_color_rgb, tuple_to_hex
from ._constants import DisplayType, DIAL_DEFAULT_ITEM
from datetime import datetime
from time import time, sleep
from PIL import Image, ImageTk
import tkinter as tk

class Renderer:
	_size = None
	_max_frames = None
	_debug = False
	_address = None
	_pizoo = None

	def __init__(self, address, pizzoo, debug):
		self._debug = debug
		self._address = address
		self._pizzoo = pizzoo

	def get_size(self):
		return self._size
	
	def get_max_frames(self):
		return self._max_frames
	
	def get_settings(self):
		raise NotImplementedError
	
	def set_brightness(self, brightness):
		raise NotImplementedError
	
	def switch(self, on=True):
		raise NotImplementedError

	def render(self, buffer, frame_speed):
		raise NotImplementedError
	
	def compile_node(self, node, parent, inherited_props, node_props):
		return None

	def compile_node_root_options(self, options):
		return []

	def render_template_items(self, items, use_cache=True):
		return None

class Pixoo64Renderer(Renderer):
	__start_countdown_time = -1
	__pic_id = None
	__url = None
	__id_limit = None
	def __init__(self, address, pizzoo, debug):
		super().__init__(address, pizzoo, debug)
		self._size = 64
		self._max_frames = 60
		self.__id_limit = 100
		self.__url = f'http://{address}/post'
		self.__pic_id = self.__request('Draw/GetHttpGifId')['PicId']
		if self.__pic_id > self.__id_limit:
			self.__reset_pic_id()

	def __request(self, endpoint, data=None):
		data = {'Command': endpoint, **(data if data else {})}
		result = post(self.__url, dumps(data)).json()
		if result['error_code'] != 0:
			raise Exception(f'Error on request {endpoint} with code {result["error_message"]}')
		return result
	
	def __reset_pic_id(self):
		try:
			self.__request('Draw/ResetHttpGifId')
			self.__pic_id = 1
		except Exception as e:
			if self._debug: print(e)

	def __send_frame(self, frame_data, speed=1000, frame_number=1, offset=0):
		return self.__request('Draw/SendHttpGif', {
			'PicNum': frame_number,
			'PicWidth': self._size,
			'PicOffset': offset,
			'PicID': self.__pic_id,
			'PicSpeed': speed,
			'PicData': b64encode(bytearray(frame_data)).decode()
		})
	
	def buzzer(self, active=0.5, inactive=0.5, duration=1):
		'''
		Plays a sound on the device buzzer.

		Parameters:
		- active (float): The time in seconds the buzzer is active.
		- inactive (float): The time in seconds the buzzer is inactive.
		- duration (float): The total time in seconds the buzzer will play.

		Returns:
		- None
		'''
		self.__request('Device/PlayBuzzer', {
			'ActiveTimeInCycle': active * 1000,
			'OffTimeInCycle': inactive * 1000,
			'PlayTotalTime': duration * 1000
		})
	
	def set_scoreboard(self, blue_score=0, red_score=0):
		'''
		Sets the scoreboard on the device for every team.

		Parameters:
		- blue_score (int): The score for the blue team.
		- red_score (int): The score for the red team.

		Returns:
		- None
		'''
		self.__request('Tools/SetScoreBoard', {
			'BlueScore': blue_score,
			'RedScore': red_score
		})

	def start_countdown(self, seconds=0):
		'''
		Creates and starts the countdown timer on the device.

		Parameters:
		- seconds (int): The amount of seconds to countdown from.

		Returns:
		- None
		'''
		minutes = int(seconds / 60)
		seconds = seconds % 60
		self.__request('Tools/SetTimer', {
			'Minute': minutes,
			'Second': seconds,
			'Status': 1
		})
		self.__start_countdown_time = time()

	def stop_countdown(self):
		'''
		Stops the countdown timer on the device.

		Parameters:
		- None

		Returns:
		- int: Elapsed time in seconds
		'''
		self.__request('Tools/SetTimer', {
			'Status': 0
		})
		return int(time() - self.__start_countdown_time)
	
	def clear_remote_text(self):
		'''
		Clears the remote text on the device.
		'''
		return self.__request('Draw/ClearHttpText')

	def switch(self, on=True):
		self.__request('Channel/OnOffScreen', {
			'OnOff': 1 if on else 0
		})

	def set_brightness(self, brightness):
		self.__request('Channel/SetBrightness', {
			'Brightness': clamp(brightness, 0, 100)
		})

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
				self._pizoo.draw_gif(background, size='auto', fill='auto')
			else:
				self._pizoo.draw_image(background)
			self._pizoo.render()
		if clear:
			self.clear_remote_text()
		processed_items = [{'TextId': index + 1, **DIAL_DEFAULT_ITEM, **item} for index, item in enumerate(items)]
		self.__request('Draw/SendHttpItemList', {
			'ItemList': processed_items
		})

	def render(self, buffer, frame_speed):
		self.__pic_id += 1
		if self.__pic_id >= self.__id_limit:
			self.__reset_pic_id()
		buffer = buffer[-self._max_frames:]
		# Because of a weird bug in the Pixoo64, we need to make sure the frame speed is not below 95 or greater than 280 (290 is the max speed)
		# frame_speed = floor(clamp(frame_speed, 95, 280))
		frame_speed = floor(clamp(frame_speed, 10, 10000))
		for i, frame in enumerate(buffer):
			self.__send_frame(frame, speed=frame_speed, frame_number=len(buffer), offset=i)

	def compile_node_root_options(self, options):
		result = []
		if options['brigthness'] is not None:
			result.append((self.set_brightness, {'brightness': options['brigthness']}))
		if options['turn_screen'] is True:
			result.append((self.switch, {}))
		if options['notification'] is True:
			result.append((self.buzzer, {'duration': 2}))
		return result
	
	def __command_atributes(self, node):
		attributes = {}
		attributes['dir'] = node.attrib.get('scroll', 'left')
		attributes['dir'] = 0 if attributes['dir'] == 'left' else 1
		try:
			attributes['font'] = int(node.attrib.get('font', '2'))
		except:
			attributes['font'] = 18 if node.attrib['font'] == 'small' else 2
		attributes['speed'] = clamp(int(node.attrib.get('speed', '100')), 1, 100)
		attributes['color'] = get_color_rgb(node.attrib.get('color', '7'))
		attributes['align'] = node.attrib.get('align', 'left')
		attributes['align'] = 1 if attributes['align'] == 'left' else 2 if attributes['align'] == 'center' else 3
		if 'update' in node.attrib:
			attributes['update_time'] = int(node.attrib['update'])
		return attributes

	def compile_node(self, node, parent, inherited_props, node_props):
		tag = node.tag
		width, height = node_props['node_size']
		abs_x, abs_y = node_props['abs_coords']
		result = None
		if tag == 'message':
			text = node.text
			attributes = self.__command_atributes(node)
			result = (DisplayType.TEXT_MESSAGE, {**attributes, 'TextString': text, 'x': abs_x, 'y': abs_y, 'TextWidth': width, 'TextHeight': height})
		elif tag == 'time':
			attributes = self.__command_atributes(node)
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
			result = (DisplayType.WEATHER_WORD, {**attributes, 'x': abs_x, 'y': abs_y, 'TextWidth': width, 'TextHeight': height})
		elif tag == 'date':
			attributes = self.__command_atributes(node)
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
		return result
	
	def render_template_items(self, items, use_cache=True):
		# workaround for a desync error with the divoom device when sending dial items
		sleep(0.2)
		items = [{'type': item[0], **item[1], 'color': tuple_to_hex(item[1]['color'])} for item in items]
		self.set_dial(items)

class ImageRenderer(Renderer):
	def __init__(self, address, pizzoo, debug, resize_factor=5, resample_method=Image.NEAREST):
		super().__init__(address, pizzoo, debug)
		self._size = 64
		self._max_frames = 60
		self._resize_factor = resize_factor
		self._resample_method = resample_method

	def switch(self, on=True):
		pass
	
	def render(self, buffer, frame_speed):
		'''
		The static render creates an image (if one frame) or a gif (if multiple frames) and then shows and returns it.
		'''
		buffer = buffer[-self._max_frames:]
		if len(buffer) == 1:
			image = Image.frombytes('RGB', (self._size, self._size), bytes(buffer[0]), 'raw')
			if self._resize_factor > 1:
				image = image.resize((self._size * self._resize_factor, self._size * self._resize_factor), resample=self._resample_method)
			image.save('temp.png')
			image.show()
		else:
			# Create gif with all frames
			images = []
			for frame in buffer:
				images.append(Image.frombytes('RGB', (self._size, self._size), bytes(frame), 'raw'))
			if self._resize_factor > 1:
				images = [image.resize((self._size * self._resize_factor, self._size * self._resize_factor), resample=self._resample_method) for image in images]
			images[0].save('temp.gif', save_all=True, append_images=images[1:], loop=0, duration=frame_speed)

	def __command_atributes(self, node):
		attributes = {}
		attributes['color'] = get_color_rgb(node.attrib.get('color', '7'))
		return attributes
	
	def compile_node(self, node, parent, inherited_props, node_props):
		tag = node.tag
		abs_x, abs_y = node_props['abs_coords']
		result = None
		if tag == 'message':
			text = node.text
			attributes = self.__command_atributes(node)
			result = (self._pizzoo.draw_text, {'text': text, 'xy': (abs_x, abs_y), **attributes})
		elif tag == 'time':
			attributes = self.__command_atributes(node)
			time_format = node.attrib.get('format', 'HH:mm:ss')
			time_format = time_format.replace('HH', '%H').replace('mm', '%M').replace('ss', '%S')
			text = datetime.now().strftime(time_format)
			result = (self._pizzoo.draw_text, {'text': text, 'xy': (abs_x, abs_y), **attributes})
		elif tag == 'temperature':
			attributes = self.__command_atributes(node)
			result = (self._pizzoo.draw_text, {'text': '30°C', 'xy': (abs_x, abs_y), **attributes})     
		elif tag == 'weather':
			attributes = self.__command_atributes(node)
			result = (self._pizzoo.draw_text, {'text': 'Sunny', 'xy': (abs_x, abs_y), **attributes})
		elif tag == 'date':
			attributes = self.__command_atributes(node)
			date_format = node.attrib.get('format', 'DD/MM/YYYY')
			date_format = date_format.replace('DD', '%d').replace('MM', '%m').replace('YYYY', '%Y').replace('WWW', '%a')
			text = datetime.now().strftime(date_format)
			result = (self._pizzoo.draw_text, {'text': text, 'xy': (abs_x, abs_y), **attributes})
		return result

class WindowRenderer(Renderer):
	def __init__(self, address, pizzoo, debug):
		super().__init__(address, pizzoo, debug)
		self._size = 64
		self._max_frames = 60
		self._resize_factor = 5
		self.__resize_size = (self._size * self._resize_factor, self._size * self._resize_factor)
		self._root = tk.Tk()
		self._root.title('Pizzoo emulator')
		self._root.geometry('{0}x{1}'.format(self.__resize_size[0], self.__resize_size[1]))
		self._root.attributes('-topmost', True)
		self.__canvas = tk.Canvas(self._root, width=self._size * self._resize_factor, height=self._size * self._resize_factor, bg='black')
		self.__canvas.pack()

		image = Image.new('RGB', (self._size, self._size), color='black')

		image = self._process_image(image)
		self.__image = self.__canvas.create_image(self.__resize_size[0] / 2, self.__resize_size[0] / 2, image=image)
		
		self._root.update()

	def switch(self, on=True):
		pass

	def _process_image(self, image):
		image = image.resize(self.__resize_size, Image.NEAREST)
		return ImageTk.PhotoImage(image)

	def render(self, buffer, frame_speed):
		'''
		The static render creates an image (if one frame) or a gif (if multiple frames) and then shows and returns it.
		'''
		buffer = buffer[-self._max_frames:]
		wh = self._size * self._resize_factor
		if len(buffer) == 1:
			image = Image.frombytes('RGB', (self._size, self._size), bytes(buffer[0]), 'raw')
			image = self._process_image(image)
			self.__canvas.itemconfig(self.__image, image=image)
		else:
			# Create gif with all frames
			images = []
			for frame in buffer:
				images.append(Image.frombytes('RGB', (self._size, self._size), bytes(frame), 'raw'))
			images = [image.resize((wh, wh), resample=Image.NEAREST) for image in images]
		self._root.update()

__all__ = (Renderer, Pixoo64Renderer, ImageRenderer, WindowRenderer)