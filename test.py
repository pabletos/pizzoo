from pizzoo import Pizzoo, WindowRenderer, ImageRenderer
from time import sleep

pizzoo = Pizzoo('192.168.50.225', debug=True)

# pizzoo.cls()

pizzoo.draw_gif('./test.gif', xy=(0, 0), size=(64, 64), loop=False)

pizzoo.render_template('''
    <pizzoo background="./test.gif">
		<rectangle x="0" y="0" width="64" height="8" color="0">
			<date format="DD" x="1" y="1" color="#ffffff" font="small"></date>
			<text x="9" y="1" color="#ffffff">-</text>
			<date format="MM" x="13" y="1" color="#ffffff" font="small"></date>
		</rectangle>
    </pizzoo>
''')