import base64
import json
from enum import IntEnum
from math import floor

from requests import post
from PIL import Image, ImageOps

from math import floor
from time import time, sleep
from xml.etree.ElementTree import ElementTree, fromstring
from ._constants import PICO_PALETTE, DIAL_DEFAULT_ITEM
from ._utils import clamp
from os.path import dirname, realpath, join


class Pizzoo:
	__buffer = []
	__current_frame = -1
	__max_frames = 60
	__url = ''
	__pic_id = 1
	__id_limit = 100
	__debug = False
	__fonts = {}
	__current_dir = dirname(realpath(__file__))

	def __init__(self, address, device='pixoo64', debug=False):
		self.__compute_device_specs(device)
		self.__url = f'http://{address}/post'
		self.__pic_id = self.__request('Draw/GetHttpGifId')['PicId']
		if self.__pic_id > self.__id_limit:
			self.__reset_pic_id()
		self.__debug = debug
		# Initialize buffer
		self.add_frame()
		# get current dir of this file:
		self.load_font('default', join(self.__current_dir, 'MatrixLight6.bdf'), False)

	def __compute_device_specs(self, device_type):
		if device_type == 'pixoo64':
			self.size = 64
			self.pixel_count = self.size * self.size
			self.__max_frames = 60
			self.__id_limit = 100
		else:
			raise ValueError('Invalid device type')
		
	def load_font(self, font_name, path, soft=True):
		if soft:
			self.__fonts[font_name] = path
		else:
			from bdfparser import Font
			self.__fonts[font_name] = Font(path)

	def load_fonts(self, fonts):
		for font_name, path in fonts.items():
			self.load_font(font_name, path)
		
	def cls(self, rgb=(0, 0, 0)):
		rgb = self.__get_color_rgb(rgb)
		self.__buffer[self.__current_frame] = [rgb[0], rgb[1], rgb[2]] * self.pixel_count

	def add_frame(self, rgb=(0, 0, 0)):
		assert self.__current_frame <= self.__max_frames, f'Frame limit reached, push before reaching {self.__max_frames} frames'
		frame = []
		for _ in range(self.pixel_count):
			frame.extend(rgb)
		self.__buffer.append(frame)
		self.__current_frame = len(self.__buffer) - 1

	def reset_buffer(self):
		self.__buffer = []
		self.__current_frame = -1
		self.add_frame()

	def draw_pixel(self, xy, color):
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
		for x in range(xy[0], xy[0] + width):
			for y in range(xy[1], xy[1] + height):
				if filled or x == xy[0] or x == xy[0] + width - 1 or y == xy[1] or y == xy[1] + height - 1:
					self.draw_pixel((x, y), color)

	def draw_circle(self, xy, radius, color, filled=True):
		for x in range(xy[0] - radius, xy[0] + radius + 1):
			for y in range(xy[1] - radius, xy[1] + radius + 1):
				if (x - xy[0]) ** 2 + (y - xy[1]) ** 2 <= radius ** 2:
					self.draw_pixel((x, y), color)
	
	def draw_image(self, image_or_path, xy=(0, 0), size='auto', resample_method=Image.NEAREST):
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

	def draw_text(self, text, xy=(0, 0), font='default', color='#FFFFFF', align=0, line_width=512):
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
		self.__pic_id += 1
		if self.__pic_id >= self.__id_limit:
			self.__reset_pic_id()
		self.__buffer = self.__buffer[-60:]
		# Because of a weird bug in the Pixoo64, we need to make sure the frame speed is not below 95 or greater than 280 (290 is the max speed)
		# frame_speed = floor(clamp(frame_speed, 95, 280))
		frame_speed = floor(clamp(frame_speed, 10, 10000))
		for i, frame in enumerate(self.__buffer):
			self.__send_frame(frame, speed=frame_speed, frame_number=len(self.__buffer), offset=i)
		self.reset_buffer()

	def set_dial(self, items, background=None, clear=True):
		if background is not None:
			path_ext = background.split('.')[-1]
			if path_ext == 'gif':
				self.draw_gif(background, size='auto', fill='auto')
			else:
				self.draw_image(background)
			self.render()
		if clear:
			self.clear_text()
		processed_items = [{'TextId': index + 1, **DIAL_DEFAULT_ITEM, **item} for index, item in enumerate(items)]
		self.__request('Draw/SendHttpItemList', {
			'ItemList': processed_items
		})

	def buzzer(self, active=0.5, inactive=0.5, duration=1):
		return self.__request('Device/PlayBuzzer', {
			'ActiveTimeInCycle': active * 1000,
			'OffTimeInCycle': inactive * 1000,
			'PlayTotalTime': duration * 1000
		})
	
	def turn_screen(self, on=True):
		self.__request('Channel/OnOffScreen', {
			'OnOff': 1 if on else 0
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
		- Elapsed time in seconds (int)
		'''
		self.__request('Tools/SetTimer', {
			'Status': 0
		})
		return int(time() - self.__start_countdown_time)
	
	def get_settings(self):
		return self.__request('Channel/GetAllConf')
	
	def clear_remote_text(self):
		return self.__request('Draw/ClearHttpText')

	def __get_color_rgb(self, color):
		if isinstance(color, tuple):
			return color
		if isinstance(color, int):
			return PICO_PALETTE[color]
		if isinstance(color, str) and color[0] == '#' and len(color) == 7:
			return tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
		raise ValueError('Invalid color format')

	def __request(self, endpoint, data=None):
		data = {'Command': endpoint, **(data if data else {})}
		result = post(self.__url, json.dumps(data)).json()
		if result['error_code'] != 0:
			raise Exception(f'Error on request {endpoint} with code {result["error_message"]}')
		return result

	def __reset_pic_id(self):
		try:
			self.__request('Draw/ResetHttpGifId')
			self.__pic_id = 1
		except Exception as e:
			if self.__debug: print(e)

	def __send_frame(self, frame_data, speed=1000, frame_number=1, offset=0):
		return self.__request('Draw/SendHttpGif', {
			'PicNum': frame_number,
			'PicWidth': self.size,
			'PicOffset': offset,
			'PicID': self.__pic_id,
			'PicSpeed': speed,
			'PicData': base64.b64encode(bytearray(frame_data)).decode()
		})

__all__ = (Pizzoo)