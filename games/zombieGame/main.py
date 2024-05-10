from pizzoo.game import PizzooGame, Sprite, distance
from pynput import keyboard
from .actors import Player, Zombie, Spitter, Car
from random import randint, random
from .constants import BASE
from os.path import join

class ZombieGame(PizzooGame):
	def __init__(self, pixoo_instance):
		super().__init__(pixoo_instance, frame_limit=60, dev=True)
		self.player = Player(0, 0, self, 0)
		self.add_instance(self.player)
		self.projectiles = []
		self.max_critters = 5
		self.init_level()
		self.create_camera(center_on=self.player)
		self.critter_spawn_ratio = {
			Spitter: 0.3,
			Zombie: 1
		}

	def init_level(self):
		self.maps.append(self.create_map(8, 16, 16))
		self.maps[0].fill(Sprite('images/tile.png', base_path=BASE, z_index=0))
		self.maps[0].add_tile(Sprite('images/road.png', base_path=BASE, z_index=1), 4, 0, span=(4, 4))
		self.maps[0].add_tile(Sprite('images/road.png', base_path=BASE, z_index=1), 4, 4, span=(4, 4))
		self.maps[0].add_tile(Sprite('images/road-right.png', base_path=BASE, z_index=1), 4, 8, span=(4, 4))
		self.maps[0].add_tile(Sprite('images/road-horizontal.png', base_path=BASE, z_index=1), 8, 8, span=(4, 4))
		self.maps[0].add_tile(Sprite('images/road-horizontal.png', base_path=BASE, z_index=1), 12, 8, span=(4, 4))
		self.add_instance(Car(40, 0, self, 1))

	def get_num_critters(self):
		return len([instance for instance in self.instances if instance.__class__.__name__ in ['Zombie', 'Spitter']])

	def spawn_critter(self):
		roll = random()
		for critter, probability in self.critter_spawn_ratio.items():
			if roll < probability:
				map_width = self.maps[self.current_map].tiles_width * self.maps[self.current_map].tile_size
				map_height = self.maps[self.current_map].tiles_height * self.maps[self.current_map].tile_size
				x, y = randint(0, map_width + 8), randint(0, map_height - 8)
				while distance((x, y), (self.player.x, self.player.y)) < 8:
					x, y = randint(0, map_width + 8), randint(0, map_height - 8)
				self.add_instance(critter(x, y, self, 1, self.player))
				break
	
	def on_press(self, key):
		key = key.char if hasattr(key, 'char') else key
		super().on_press(key)
		try:
			if key == keyboard.Key.esc:
				self.stop()
				self.pixoo.set_screen_off()
		except AttributeError as e:
			print(e) 
			pass

	def car_ended(self):
		return len([instance for instance in self.instances if instance.__class__.__name__ == 'Car']) == 0

	def step(self):
		super().step()
		if self.get_num_critters() < self.max_critters:
			self.spawn_critter()
		if self.car_ended():
			self.timer('car_timer', lambda: self.add_instance(Car(40, 0, self, 1)), random() * 30 + 5)

	def draw_ui(self):
		for i in range(0, self.player.health):
			self.pizzoo.draw_image(join(BASE, 'images/heart.png'), xy=(48 + i * 5, 1))
		for i in range(0, self.player.bullets):
			self.pizzoo.draw_image(join(BASE, 'images/bullet.png'), xy=(1 + i * 3, 1))