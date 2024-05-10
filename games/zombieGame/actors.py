from pizzoo.game import Actor, distance, Path
from pynput import keyboard
from .constants import BASE

class Player(Actor):
	def __init__(self, x, y, game, z_index):
		frame_src = [
			'images/sprite.png',
			'images/sprite_right.png',
			'images/sprite_left.png',
			'images/sprite_up.png'
		]
		super().__init__(x, y, frame_src, game, base_path=BASE, z_index=z_index)
		self.health = 3
		self.bullets = 6
		self.invincible = 0
		self.speed = [1, 1]
		self.direction = [0, 0]
		self.g = game

	def on_press(self, key):
		if key == 'd':
			self.speed[0] += 1
			self.direction = [1, 0]
			self.sprite.set_frame(1)
		elif key == 'a':
			self.speed[0] -= 1
			self.direction = [-1, 0]
			self.sprite.set_frame(2)
		elif key == 'w':
			self.speed[1] -= 1
			self.direction = [0, -1]
			self.sprite.set_frame(3)
		elif key == 's':
			self.speed[1] += 1
			self.direction = [0, 1]
			self.sprite.set_frame(0)
		if key == keyboard.Key.space:
			if self.bullets == 0:
				return
			pr_x = self.bounding_box_size[0] if self.direction[0] == 1 else 0
			pr_x = int(self.bounding_box_size[0] / 2) - 1 if self.direction[0] == 0 else pr_x
			self.g.add_instance(
				Projectile(
					self.x + pr_x,
					self.y + int(self.bounding_box_size[1] / 2),
					self.g, 2,
					self.direction,
					interacts_with=['Zombie', 'Spitter']
				)
			)
			self.bullets -= 1

	def step(self):
		# Update game state
		map = self.g.maps[self.g.current_map]
		map_width = map.tiles_width * map.tile_size
		map_height = map.tiles_height * map.tile_size
		if self.invincible > 0:
			self.invincible -= 1
		new_x = self.x + self.speed[0]
		new_y = self.y + self.speed[1]
		if new_x >= map_width:
			new_x = 0
		elif new_x < 0:
			new_x = map_width - 1
		if new_y >= map_height:
			new_y = 0
		elif new_y < 0:
			new_y = map_height - 1
		self.x = new_x
		self.y = new_y
		self.speed = [0, 0]

class Zombie(Actor):
	def __init__(self, x, y, game, z_index, player):
		frame_src = [
			'images/npc.png',
			'images/npc_right.png',
			'images/npc_left.png',
			'images/npc_up.png'
		]
		super().__init__(x, y, frame_src, game, base_path=BASE, z_index=z_index)
		self.health = 1
		self.speed = [.25, .25]
		self.direction = [0, 0]
		self.g = game
		self.player = player

	def collisions(self):
		players_collided = self.check_collisions('Player')
		for player in players_collided:
			if player.invincible == 0 and self.x == player.x and self.y == player.y:
				player.health -= 1
				player.invincible = 10
				if player.health == 0:
					player.destroy()
			
	def step(self):
		if self.x > self.player.x:
			self.x -= self.speed[0]
			self.direction[0] = -1
			self.sprite.set_frame(2)
		elif self.x < self.player.x:
			self.x += self.speed[0]
			self.direction[0] = 1
			self.sprite.set_frame(1)
		if self.y > self.player.y:
			self.y -= self.speed[1]
			self.direction[1] = -1
			self.sprite.set_frame(3)
		elif self.y < self.player.y:
			self.y += self.speed[1]
			self.direction[1] = 1
			self.sprite.set_frame(0)

class Spitter(Actor):
	def __init__(self, x, y, game,  z_index, player):
		frame_src = [
			'images/npc.png',
			'images/npc_right.png',
			'images/npc_left.png',
			'images/npc_up.png'
		]
		super().__init__(x, y, frame_src, game, base_path=BASE, z_index=z_index)
		self.max_shoot_distance = 32
		self.health = 1
		self.speed = [.25, .25]
		self.direction = [0, 0]
		self.g = game
		self.player = player
		self.shoot_cooldown = 0

	def collisions(self):
		players_collided = self.check_collisions('Player')
		for player in players_collided:
			if player.invincible == 0 and self.x == player.x and self.y == player.y:
				player.health -= 1
				player.invincible = 10
				if player.health == 0:
					player.destroy()
	def step(self):
		if self.shoot_cooldown > 0:
			self.shoot_cooldown -= 1
		if distance((self.x, self.y), (self.player.x, self.player.y)) > self.max_shoot_distance:
			if self.x > self.player.x:
				self.x -= self.speed[0]
				self.direction[0] = -1
				self.sprite.set_frame(2)
			elif self.x < self.player.x:
				self.x += self.speed[0]
				self.direction[0] = 1
				self.sprite.set_frame(1)
			if self.y > self.player.y:
				self.y -= self.speed[1]
				self.direction[1] = -1
				self.sprite.set_frame(3)
			elif self.y < self.player.y:
				self.y += self.speed[1]
				self.direction[1] = 1
				self.sprite.set_frame(0)
		elif self.shoot_cooldown == 0:
			# Shoot projectile towards player
			self.shoot_cooldown = 20
			if self.player.x > self.x:
				self.g.add_instance(
					Projectile(
						self.x + self.bounding_box_size[0],
						self.y + int(self.bounding_box_size[1] / 2),
						self.g, 2,
						(1, 0),
						frame='spit.png',
						interacts_with=['Player']
					)
				)
			elif self.player.x < self.x:
				self.g.add_instance(
					Projectile(
						self.x,
						self.y + int(self.bounding_box_size[1] / 2),
						self.g, 2,
						(-1, 0),
						frame='spit.png',
						interacts_with=['Player']
					)
				)

class Projectile(Actor):
	def __init__(self, x, y, game, z_index, direction, frame='projectile.png', interacts_with=None):
		frame_src = [
			'images/%s' % frame
		]
		super().__init__(x, y, frame_src, game, base_path=BASE, z_index=z_index)
		self.speed = 2
		self.direction = direction
		self.g = game
		self.interacts_with = interacts_with

	def collisions(self):
		targets_collided = self.check_collisions(self.interacts_with)
		for target in [t for t in targets_collided if hasattr(t, 'health')]:
			target.health -= 1
			if target.health == 0:
				target.destroy()
			self.destroy()

	def step(self):
		self.x += self.speed * self.direction[0]
		self.y += self.speed * self.direction[1]
		current_map = self.g.maps[self.g.current_map]
		max_width = current_map.tiles_width * current_map.tile_size
		max_height = current_map.tiles_height * current_map.tile_size
		if self.x < 0 or self.x >= max_width or self.y < 0 or self.y >= max_height:
			self.destroy()

class Car(Actor):
	def __init__(self, x, y, game, z_index):
		frame_src = [
			'images/car.png',
			'images/car_alt.png'
		]
		super().__init__(x, y, frame_src, game, base_path=BASE, z_index=z_index)
		self.speed = 1.5
		self.direction = [0, 0]
		self.g = game
		self.path = Path([(5, 0), (5, 9), (12, 9)], tile_size=8)

	def step(self):
		target = self.path.next(self.x, self.y, coords=True)
		if target == None:
			self.destroy()
			return
		if target[0] > self.x:
			self.x += self.speed
			self.direction[0] = 1
			self.sprite.set_frame(1)
		elif target[0] < self.x:
			self.x -= self.speed
			self.direction[0] = -1
			self.sprite.set_frame(0)
		elif target[1] > self.y:
			self.y += self.speed
			self.direction[1] = 1
			self.sprite.set_frame(0)
		elif target[1] < self.y:
			self.y -= self.speed
			self.direction[1] = -1
			self.sprite.set_frame(0)