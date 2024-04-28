from ._constants import PICO_PALETTE

def clamp(n, minn, maxn):
	return max(min(maxn, n), minn)

def get_color_rgb(color):
	if isinstance(color, tuple):
		return color
	if isinstance(color, str):
		if color.isdigit():
			return PICO_PALETTE[int(color)]
		if color[0] == '#' and len(color) == 7:
			return tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
		if color[0] == '(' and color[-1] == ')':
			return tuple(int(x) for x in color[1:-1].split(','))
	if isinstance(color, int):
		return PICO_PALETTE[color]
	raise ValueError('Invalid color format')
	return color

def tuple_to_hex(color_tuple):
	return '#%02x%02x%02x' % color_tuple

__all__ = (clamp, get_color_rgb, tuple_to_hex)