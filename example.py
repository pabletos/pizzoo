from pizzoo import Pizzoo, WindowRenderer, ImageRenderer
from time import sleep

'''Create the main object and the connection to the Pixoo device'''
pizzoo = Pizzoo('192.168.50.225', debug=True)
pizzoo.switch(on=True) # Turn on the Pixoo device screen

def example_draw_pixel():
	'''
	Draw three simple pixels on the Pixoo device.
	'''
	pizzoo.cls() # Clear the screen with black color (By default)
	pizzoo.draw_pixel((30, 31), '#ff0000') # Red pixel, using the hex color format
	pizzoo.draw_pixel((31, 31), (0, 255, 0)) # Green pixel, using the RGB tuple format
	pizzoo.draw_pixel((32, 31), 12) # An integer color between 0 and 15 is a pico-8 palette color (https://lospec.com/palette-list/pico-8)
	pizzoo.render() # Render the frame to the Pixoo device, this is mandatory to see the changes on the device

def example_draw_shapes():
	'''
	Draw different shapes on the Pixoo device.
	Shapes can be drawn with different colors and filled or not.
	'''
	pizzoo.cls()
	pizzoo.draw_circle((31, 31), 10, '#00ff00', filled=True) # Green circle, filled
	pizzoo.draw_rectangle((26, 26), 11, 11, '#ff0000', filled=False) # Red rectangle, not filled
	pizzoo.draw_line((31, 0), (31, 63), '#0000ff') # Blue line
	pizzoo.draw_line((0, 31), (63, 31), (255, 255, 0)) # Yellow line, tuple rgb color format
	pizzoo.render()

def example_draw_text():
	'''
	Draw text with different fonts and colors.
	The default bdf font is used to draw text on the Pixoo device.
	New fonts can be added to the running instance using the load_font method (Only on .bdf extension).
	Text then can be drawn on a given position, with the defined font and an optional max line width (So it will be wrapped).
	'''
	pizzoo.load_font('artos', './files/ArtosSans-8.bdf')
	pizzoo.load_font('amstrad', './files/amstrad_cpc_extended.bdf')
	pizzoo.cls((255, 255, 255))
	pizzoo.draw_text('Amstrad', xy=(2, 2), font='amstrad', color='#00ff00') # Custom amstrad font, no wrap is defined
	pizzoo.draw_text('Artos', xy=(2, 12), font='artos', color=(255, 0, 0), line_width='auto') # Custom artos font, wrap is 'auto' so full device width (64px)
	pizzoo.draw_text('This is a pretty big text using the default font for the library.', xy=(1, 24), color='#000000', line_width=62) # Default font, custom line width
	pizzoo.render()

def example_draw_image():
	'''
	Draw an image on the current buffer.
	Images can be drawn with a given position and size.
	'''
	pizzoo.cls()
	pizzoo.draw_image('./files/test_image.png', xy=(0, 0)) # Draw a 16x16 image on the center of the screen
	pizzoo.draw_image('./files/test_image.png', xy=(16, 16), size=(32, 32)) # Image can be resized to any width and/or height
	pizzoo.render()

def example_draw_gif():
	'''
	The Pizzoo library uses an animation buffer, so it can also draw gifs on the device.
	Gifs can be drawn with a given position and size, as any other image.
	'''
	pizzoo.cls()
	pizzoo.draw_gif('./files/test_gif.gif', xy=(15, 15), size=(32, 32), loop=True) # Draw a gif on the center of the screen
	pizzoo.render()

def example_scoreboard():
	'''
	Activate the scoreboard on the Pixoo device.
	No cls or render method is needed as this is a built-in method of the Pixoo64 device.
	'''
	pizzoo.set_scoreboard(1, 2) # Set the scoreboard with the numbers 1 for the Blue team and 2 for the Red team

def example_buzzer():
	'''
	Play a sound on the Pixoo device.
	The buzzer method can play a sound with a given frequency and duration.
	'''
	pizzoo.buzzer(1, 1, 4) # Play a sound with a frequency of 1 second ON, 1 second OFF and a duration of 4 seconds.

def example_countdown():
	'''
	Activate the countdown on the Pixoo device.
	No cls or render method is needed as this is a built-in method of the Pixoo64 device.
	When stopping the countdown, the elapsed time is also returned by the method.
	'''
	from time import sleep
	pizzoo.start_countdown(10) # Sets a countdown of 5 seconds
	sleep(5)
	elapsed_time = pizzoo.stop_countdown() # Stops the countdown prematurely and returns the elapsed time
	print(f'Elapsed time: {elapsed_time} seconds')

def example_template():
	'''
	Render an XML template on the Pixoo device.
	'''
	pizzoo.load_font('amstrad', './files/amstrad_cpc_extended.bdf')
	pizzoo.render_template('''
		<pizzoo>
			<rectangle x="0" y="0" width="100%" height="100%" color="8" filled="true">
				<section x="0" y="2">
					<date format="DD" x="1" color="#ffc107" font="small"></date>
					<text x="9" color="#ffc107">-</text>
					<date format="MM" x="13" color="#ffc107" font="small"></date>
					<time format="HH:mm" x="26" font="small"></time>
					<date format="WWW" width="63" align="right" color="#ffc107" font="small"></date>
				</section>
				<section x="5" y="10" width="53" height="43">
					<rectangle x="0" y="0" width="100%" height="100%" color="#FFFFFF" filled="true" />
					<section x="1" y="1" width="51" height="51">
						<text x="0" y="0" color="#000000" wrap="true">Long text wrapped</text>
						<text x="10" y="80%" shadow="diagonal" color="#FF0000" font="amstrad">Cool</text>
						<image x="17" y="40%" src="./files/test_image.png" />
					</section>
				</section>
			</rectangle>
		</pizzoo>
	''')
	
def power_off():
	'''
	Turn off the Pixoo device.
	'''
	pizzoo.turn_screen(on=False)

if __name__ == '__main__':
	# create a terminal menu to select the example to run
	selected_option = None
	menu = {
		'1': {'Draw Pixel': example_draw_pixel},
		'2': {'Draw Shapes': example_draw_shapes},
		'3': {'Draw Text': example_draw_text},
		'4': {'Draw Image': example_draw_image},
		'5': {'Draw Gif': example_draw_gif},
		'6': {'Scoreboard': example_scoreboard},
		'7': {'Buzzer': example_buzzer},
		'8': {'Countdown': example_countdown},
		'9': {'Render an XML template': example_template}
	}
	print('Select an example to run:')
	for key, value in menu.items():
		print(f'{key}. {list(value.keys())[0]}')
	print('0. Exit')
	option = input('Option: ')
	selected_option = option
	if option in menu:
		menu[option][list(menu[option].keys())[0]]()
	elif option == '0':
		print('Exiting...')
		power_off()
	else:
		print('Invalid option, please try again.')
	sleep(3)

