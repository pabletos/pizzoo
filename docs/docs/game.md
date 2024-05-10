# Building your first game

!!! warning "**This feature and the documentation is still a work in progress, if you have any feedback or suggestions, please let us know!**"

	You can find a working example [here in the repo](https://github.com/pabletos/pizzoo/tree/main/games/zombieGame). I recommend that you first inspect the code and play with it, every part of the engine was used here where developing it.

Included with this library is also a pretty simple `Game` class that can be used to create little games that can be played on a renderer (With direct support for the Pixoo64 device).

!!! info "**Game framerate on the Pixoo64 is really low**"

    So this is just a cool feature that can be used for more static games like card games and not so much oriented to any kind of adventure or action oriented game. This, of course, can be different for any other renderer, as technical specs varies a lot.

## Game basics

The micro-game engine included with Pizzoo follows a common approach at game development that can be found in great or lesser extents in engines like Gamemaker, pico-8 or pygame. 

``` mermaid
graph LR
  A[__init__] --> B["start()"];
  B --> C{is running?};
  C -->|Yes| D["step()"];
  D --> E["draw()"];
  E --> F["draw_ui()"];
  F --> G["pizzoo render()"];
  G --> H["_check_timers()"];
  H --> C;
```

Calling to the `stop` method will pause the running game instance and turn off the selected renderer (If the `switch`` method is implemented on said renderer).

Creating a new game starts by extending the base class `Game` and initializing:

```python
from pizzoo.game import PizzooGame

class MyGame(PizzooGame):
	def __init__(self, pizzoo_instance, another_param):
		super().__init__(pizzoo_instance, frame_limit=60, dev=False)
		self.your_attribute = another_param
```

!!! info "**Don't forget to always call the super method, otherwise the framework may not work correctly**"

Any game is comprised of instances that react to the game world, these instances are called actors; Classes that have some directions on how to react for every step, collision, button press...etc. You can extend your own actors importing also the `Actor` class. So lets say you want to create your main character:

```python
from pizzoo.game import Actor

class Player(Actor):
	def __init__(self,,x, y, game, z_index):
		super().__init__(x, y, frame_src, game, base_path=BASE, z_index=z_index)
		self.lifes = 3
	
	def collisions(self):
		# Called after every instance step to check collisions using the check_collisions own method
		npcs_collided = self.check_collisions('NPC')
		for npc in npcs_collided:
			# npc variable holds the collided instance
			self.lifes -= 1
	
	def on_press(self, key):
		# Implement to make the actor react to a key press
	
	def step(self):
		# Implement it to create a logic for how the actor should change its state every game step
		if self.lifes <= 0:
			self.g.end_game()
			self.destroy()
```

This is a simple logic in wich the actor is static but checks every step if there are collisions with any instance of `NPC` class. If any collision is detected, a life is substracted from the total lifes. If in the next step the numbers of lifes is zero or lessen it will call a custom implemented `end_game` method on the main `MyGame` class and then will destroy itself.

## The step loop

!!! abstract "Work in progress!"

## Draw methods

!!! abstract "Work in progress!"

## Maps and cameras

!!! abstract "Work in progress!"

## Controls handling

!!! abstract "Work in progress!"