from time import time, perf_counter
from PIL import Image, ImageSequence
from math import ceil, floor
from os.path import join

def tile_to_coords(tile_size, tile_x, tile_y):
	return (tile_x * tile_size, tile_y * tile_size)

def coords_to_tile(tile_size, x, y, use_ceil=False):
	round_method = ceil if use_ceil else floor
	return (round_method(x / tile_size), round_method(y / tile_size))

def distance(a, b):
	return ((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** (1 / 2)

class Camera:
	def __init__(self, game, x, y, center_on=None):
		self.g = game
		self.x = x
		self.y = y
		self.width = 64
		self.height = 64
		self.center_on = center_on
		if self.center_on is not None:
			self.center(self.center_on)
	
	def center(self, target):
		current_map = self.g.maps[self.g.current_map]
		current_map_width = current_map.tiles_width * current_map.tile_size
		current_map_height = current_map.tiles_height * current_map.tile_size
		self.x = target.x - int(self.width / 2)
		self.y = target.y - int(self.height / 2)
		if self.x < 0:
			self.x = 0
		elif self.x + self.width > current_map_width:
			self.x = current_map_width - self.width
		if self.y < 0:
			self.y = 0
		elif self.y + self.height > current_map_height:
			self.y = current_map_height - self.height
	
	def step(self):
		if self.center_on is None:
			return
		self.center(self.center_on)

class Map:
	def __init__(self, tile_size, tiles_width, tiles_height):
		self.tile_size = tile_size
		self.tiles_width = tiles_width
		self.tiles_height = tiles_height
		# create tiles by value not by reference
		self.tiles = [[None for x in range(tiles_width)] for y in range(tiles_height)]
		self.map_image = None
		self.map_memo = {}
	
	def draw(self, pizzoo, camera):
		'''Draws the map on the screen using a cropped image of the map image and a memoization based on the camera position'''
		if self.map_image is None:
			return
		# check map memo
		result = None
		index = (camera.x, camera.y, camera.width, camera.height)
		if not index in self.map_memo:
			result = self.map_image.crop((camera.x, camera.y, camera.x + camera.width, camera.y + camera.height))
			self.map_memo[index] = result
		else:
			result = self.map_memo[index]
		pizzoo.draw_image(result, (0, 0))

	def fill(self, tile):
		for y in range(self.tiles_height):
			for x in range(self.tiles_width):
				if self.tiles[y][x] is None:
					self.tiles[y][x] = []
				self.tiles[y][x].append(tile)
				self.tiles[y][x].sort(key=lambda x: x.z_index)
		self.generate_map_image()

	def generate_map_image(self):
		self.map_memo = {}
		self.map_image = Image.new('RGB', (self.tiles_width * self.tile_size, self.tiles_height * self.tile_size))
		for y in range(self.tiles_height):
			for x in range(self.tiles_width):
				if self.tiles[y][x] is not None:
					for tile in self.tiles[y][x]:
						tile_x, tile_y = tile_to_coords(self.tile_size, x, y)
						self.map_image.paste(tile.get_frame(), (tile_x, tile_y))
		return self.map_image

	def add_tile_at(self, tile, x, y):
		if self.tiles[y][x] is None:
			self.tiles[y][x] = []
		self.tiles[y][x].append(tile)
		self.tiles[y][x].sort(key=lambda x: x.z_index)
	
	def add_tile(self, tile, x, y, span=(0, 0)):
		for i in range(span[0]):
			for j in range(span[1]):
				self.add_tile_at(Sprite(tile.frame_src, current_frame=tile.current_frame, base_path=tile.base_path, offset=(i * self.tile_size, j * self.tile_size, self.tile_size), z_index=1), x + i, y + j)
		self.generate_map_image()

class Path():
	def __init__(self, nodes, current=0, tile_size=1, closed=False):
		self.nodes = nodes
		self.closed = closed
		self.tile_size = tile_size
		self.current = current
		self.has_ended = False

	def next(self, x, y, coords=False):
		'''
		Returns the next node in the path, if the path is closed, it will return to the first node when it reaches the end.

		Parameters:
		- x: the x coordinate of the object that is following the path
		- y: the y coordinate of the object that is following the path
		- coords: if True, x and y will be treated as coordinates and result will be a tuple of coordinates, otherwise it will return a tuple of tile indexes
		'''
		if self.has_ended:
			return None
		if coords:
			x, y = coords_to_tile(self.tile_size, x, y)
		if self.current >= len(self.nodes):
			if self.closed:
				self.current = 0
			else:
				self.has_ended = True
				return None
		if self.nodes[self.current][0] == x and self.nodes[self.current][1] == y:
			self.current += 1
			if self.current >= len(self.nodes):
				if self.closed:
					self.current = 0
				else:
					self.has_ended = True
					return None
		return self.nodes[self.current] if not coords else tile_to_coords(self.tile_size, self.nodes[self.current][0], self.nodes[self.current][1])		
	
	def prev(self, x, y, coords=False):
		'''
		Returns the previous node in the path, if the path is closed, it will return to the last node when it reaches the beginning.

		Parameters:
		- x: the x coordinate of the object that is following the path
		- y: the y coordinate of the object that is following the path
		- coords: if True, x and y will be treated as coordinates and result will be a tuple of coordinates, otherwise it will return a tuple of tile indexes
		'''
		if self.has_ended:
			return None
		if coords:
			x, y = coords_to_tile(self.tile_size, x, y)
		if self.current < 0:
			if self.closed:
				self.current = len(self.nodes) - 1
			else:
				self.has_ended = True
				return None
		if self.nodes[self.current][0] == x and self.nodes[self.current][1] == y:
			self.current -= 1
			if self.current < 0:
				if self.closed:
					self.current = len(self.nodes) - 1
				else:
					self.has_ended = True
					return None
		return self.nodes[self.current] if not coords else tile_to_coords(self.tile_size, self.nodes[self.current][0], self.nodes[self.current][1])


class PizzooGame:
	def __init__(self, pizzoo, frame_limit=5, dev=False):
		from pynput import keyboard
		self.pizzoo = pizzoo
		self.listener = keyboard.Listener(on_press=self.on_press)
		self.running = False
		self.frame_limit = frame_limit
		self.step_time = 1 / self.frame_limit
		self.timers = {}
		self.instances = []
		# maps is an array of maps, an every map is a multidimensional array of tiles (like a matrix)
		self.maps = []
		self.current_map = 0
		self.camera = Camera(self, 0, 0)
		self.dev = dev

	def create_camera(self, x=0, y=0, center_on=None):
		self.camera = Camera(self, x, y, center_on)

	def create_map(self, tile_size, tiles_width, tiles_height):
		'''Creates a new map with a tile size and a width and height in tiles'''
		return Map(tile_size, tiles_width, tiles_height)

	def add_instance(self, instance):
		self.instances.append(instance)
		self.instances.sort(key=lambda x: x.z_index)

	def check_collision_point(self, x, y, object_x, object_y, size):
		if x >= object_x and x <= object_x + size:
			if y >= object_y and y <= object_y + size:
				return True
		return False
	
	def check_timers(self, now):
		new_timers = {}
		for name, timer in self.timers.items():
			if now - timer['last'] >= timer['interval']:
				timer['last'] = now
				timer['callback']()
				if timer['repeat']:
					new_timers[name] = timer
			else:
				new_timers[name] = timer
		self.timers = new_timers

	def check_collisions(self, target, class_names=None):
		if class_names is None:
			filtered = self.instances
		else:
			if type(class_names) != list:
				class_names = [class_names]
			filtered = [instance for instance in self.instances if instance.solid and instance.__class__.__name__ in class_names]
		collision_list = []
		for instance in filtered:
			if self.collision(target, instance):
				collision_list.append(instance)
		return collision_list

	def collision(self, source, target):
		if source.x >= target.x and source.x <= target.x + target.bounding_box_size[0]:
			if source.y >= target.y and source.y <= target.y + target.bounding_box_size[1]:
				return True
		return False

	def draw(self):
		self.pizzoo.cls()
		self.maps[self.current_map].draw(self.pizzoo, self.camera)
		visible_instances = [instance for instance in self.instances if instance.visible]
		'''Render instances relative to the camera'''
		for instance in visible_instances:
			self.pizzoo.draw_image(instance.sprite.get_frame(), (int(instance.x - self.camera.x), int(instance.y - self.camera.y)))

	def draw_ui(self):
		pass

	def remove_instance(self, instance):
		if instance not in self.instances:
			return
		self.instances.remove(instance)
		self.instances.sort(key=lambda x: x.z_index)
		return instance
	
	def remove_timer(self, name):
		if name not in self.timers:
			return
		selected = self.timers[name]
		del self.timers[name]
		return selected
	
	def run_task(self):
		self.step()
		self.draw()
		self.draw_ui()
		self.pizzoo.render()
		self.check_timers(time())

	def run(self):
		prev_time = perf_counter()
		current_time = prev_time
		count = 0
		accum = 0
		while self.running:
			prev_time = current_time
			current_time = perf_counter()
			dt = current_time - prev_time
			self.run_task()
			if self.dev:
				accum += dt
				count += 1
				if accum >= 1.0:
					accum -= 1.0
					print(f'FPS: {count}')
					count = 0
			while perf_counter() < (current_time + self.step_time):
				pass

	def start(self):
		self.pizzoo.switch()
		self.listener.start()
		self.running = True
		self.run()

	def stop(self):
		self.running = False
		self.listener.stop()
		self.pizzoo.switch(False)

	def step(self):
		for instance in self.instances:
			instance.step()
			instance.collisions()
		self.camera.step()

	def timer(self, name, callback, interval, repeat=False, force=False):
		if name in self.timers and not force:
			return
		self.timers[name] = {
			'interval': interval,
			'callback': callback,
			'last': time(),
			'repeat': repeat
		}

	def timer_exists(self, name):
		return name in self.timers

	def on_press(self, key):
		key = key.char if hasattr(key, 'char') else key
		try:
			for instance in self.instances:
				instance.on_press(key)
		except AttributeError as e:
			print(e) 
			pass

class Sprite:
	def __init__(self, frame_src, base_path=None, current_frame=0, z_index=0, offset=(0, 0, 0)):
		'''
		frame_src can be a list of paths to images or an iterable of images (like a gif)
		'''
		self.base_path = base_path
		self.frame_src = frame_src
		self.frames = self.create_frames(frame_src, offset, base_path)
		self.current_frame = current_frame
		self.z_index = z_index

	def create_frames(self, frame_src, offset, base_path):
		frames = []
		if isinstance(frame_src, str):
			if base_path is not None:
				frame_src = join(base_path, frame_src)
			image = Image.open(frame_src)
			if offset != (0, 0, 0):
				image = image.crop((offset[0], offset[1], offset[0] + offset[2], offset[1] + offset[2]))
			for frame in ImageSequence.Iterator(image):
				frames.append(frame)
		else:
			for frame in frame_src:
				if base_path is not None:
					frame = join(base_path, frame)
				image = Image.open(frame)
				if offset != (0, 0, 0):
					image = image.crop((offset[0], offset[1], offset[0] + offset[2], offset[1] + offset[2]))
				frames.append(image)
		return frames
	
	def size(self):
		return self.frames[self.current_frame].size
			
	def next_frame(self):
		if self.current_frame + 1 >= len(self.frames):
			self.current_frame = 0
		else:
			self.current_frame += 1

	def get_frame(self, index=None):
		if index is not None:
			return self.frames[index]
		return self.frames[self.current_frame]
	
	def set_frame(self, index):
		self.current_frame = index
	
	def __getitem__(self, key):
		return self.frames[key]
	
	def __len__(self):
		return len(self.frames)

class Actor:
	def __init__(self, x, y, frame_src, game, base_path=None, z_index=0, bounding_box_size=None, visible=True, solid=True):
		self.x = x
		self.y = y
		self.sprite = Sprite(frame_src, base_path=base_path)
		self.z_index = z_index
		self.visible = visible
		self.solid = solid
		self.g = game
		self.bounding_box_size = bounding_box_size if bounding_box_size is not None else self.sprite.size()

	def check_collisions(self, class_names=None):
		return self.g.check_collisions(self, class_names)
	
	def collisions(self):
		pass
	
	def on_press(self, key):
		pass
	
	def step(self):
		pass

	def destroy(self):
		self.g.remove_instance(self)

__all__ = (PizzooGame, Sprite, Actor, Path, Camera, Map, tile_to_coords, coords_to_tile, distance)