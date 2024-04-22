from enum import IntEnum

class DisplayType(IntEnum):
    SECOND = 1
    MINUTE = 2
    HOUR = 3
    TIME_AM_PM = 4
    HOUR_MIN = 5
    HOUR_MIN_SEC = 6
    YEAR = 7
    DAY = 8
    MONTH = 9
    MONTH_YEAR = 10
    ENG_MONTH_DOT_DAY = 11
    DAY_MONTH_YEAR = 12
    ENG_WEEK_TWO = 13
    ENG_WEEK_THREE = 14
    ENG_WEEK_FULL = 15
    ENG_MONTH = 16
    TEMP_DIGIT = 17
    TODAY_MAX_TEMP = 18
    TODAY_MIN_TEMP = 19
    WEATHER_WORD = 20
    NOISE_DIGIT = 21
    TEXT_MESSAGE = 22
    NET_TEXT_MESSAGE = 23

class DIAL_ALIGN:
    LEFT = 1
    CENTER = 2
    RIGHT = 3

PICO_PALETTE = [
	(0, 0, 0),
	(29, 43, 83),
	(126, 37, 83),
	(0, 135, 81),
	(171, 82, 54),
	(95, 87, 79),
	(194, 195, 199),
	(255, 241, 232),
	(255, 0, 77),
	(255, 163, 0),
	(255, 236, 39),
	(0, 228, 54),
	(41, 173, 255),
	(131, 118, 156),
	(255, 119, 168),
	(255, 204, 170)
]

PICO_HEX_PALETTE = [
	'#000000',
	'#1D2B53',
	'#7E2553',
	'#008751',
	'#AB5236',
	'#5F574F',
	'#C2C3C7',
	'#FFF1E8',
	'#FF004D',
	'#FFA300',
	'#FFEC27',
	'#00E436',
	'#29ADFF',
	'#83769C',
	'#FF77A8',
	'#FFCCAA'
];

DIAL_DEFAULT_ITEM = {
	'x': 0,
	'y': 0,
	'dir': DIAL_ALIGN.LEFT,
	'font': 32,
	'TextWidth': 64,
	'Textheight': 64,
	'TextString': '',
	'speed': 100,
	'color': '#FFFFFF',
	'align': 0,
	'update_time': 60
}

__all__ = (PICO_PALETTE, PICO_HEX_PALETTE, DisplayType, DIAL_ALIGN, DIAL_DEFAULT_ITEM)
