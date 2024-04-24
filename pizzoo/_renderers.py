from json import dumps
from requests import post
from base64 import b64encode
from math import floor
from ._utils import clamp
from time import time
from PIL import Image, ImageTk, ImageDraw
import tkinter as tk

class Renderer:
	_size = None
	_max_frames = None
	_debug = False
	_address = None

	def __init__(self, address, debug):
		self._debug = debug
		self._address = address

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

class Pixoo64Renderer(Renderer):
	__start_countdown_time = -1
	__pic_id = None
	__url = None
	__id_limit = None
	def __init__(self, address, debug):
		super().__init__(address, debug)
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

class ImageRenderer(Renderer):
	def __init__(self, address, debug, resize_factor=5, resample_method=Image.NEAREST):
		super().__init__(address, debug)
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

class WindowRenderer(Renderer):
	def __init__(self, address, debug):
		super().__init__(address, debug)
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