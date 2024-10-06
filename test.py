from pizzoo import Pizzoo, WindowRenderer, ImageRenderer
from time import sleep

pizzoo = Pizzoo('192.168.50.225', debug=True)

# pizzoo.cls()

pizzoo.draw_gif('./test.gif', xy=(0, 0), size=(64, 64), loop=False)

pizzoo.render_template('''
    <pizzoo background="./test.gif">
        <date format="DD" x="1" y="1" color="#ffffff" font="small"></date>
    </pizzoo>
''')