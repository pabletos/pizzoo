'''
This code is directly extracted from Cat-Printer Core from the [Cat-Printer](https://github.com/NaitLee/Cat-Printer) repo. And
it's used to control the printer device. Here the important parts are adapted to create a new renderer for cat printers.

Copyright © 2021-2023 NaitLee Soft. All rights reserved.
'''

from abc import ABCMeta, abstractmethod
import asyncio
import os
import io
import sys
import asyncio
import zipfile

try:
	from bleak import BleakClient, BleakScanner
	from bleak.backends.device import BLEDevice
	from bleak.exc import BleakError, BleakDBusError
except ImportError:
	print('bleak not found, catprinter disabled, please install it')

# helpers
def flip(buffer, width, height, horizontally=False, vertically=True, *, overwrite=False):
	'Flip the bitmap data'
	buffer.seek(0)
	if not horizontally and not vertically:
		return buffer
	data_width = width // 8
	result_0 = io.BytesIO()
	if horizontally:
		while data := buffer.read(data_width):
			data = bytearray(map(reverse_bits, data))
			data.reverse()
			result_0.write(data)
		result_0.seek(0)
	else:
		result_0 = buffer
	result_1 = io.BytesIO()
	if vertically:
		for i in range(height - 1, -1, -1):
			result_0.seek(i * data_width)
			data = result_0.read(data_width)
			result_1.write(data)
		result_1.seek(0)
	else:
		result_1 = result_0
	buffer.seek(0)
	if overwrite:
		while data := result_1.read(data_width):
			buffer.write(data)
		buffer.seek(0)
	return result_1

crc8_table = [
	0x00, 0x07, 0x0e, 0x09, 0x1c, 0x1b, 0x12, 0x15, 0x38, 0x3f, 0x36, 0x31,
	0x24, 0x23, 0x2a, 0x2d, 0x70, 0x77, 0x7e, 0x79, 0x6c, 0x6b, 0x62, 0x65,
	0x48, 0x4f, 0x46, 0x41, 0x54, 0x53, 0x5a, 0x5d, 0xe0, 0xe7, 0xee, 0xe9,
	0xfc, 0xfb, 0xf2, 0xf5, 0xd8, 0xdf, 0xd6, 0xd1, 0xc4, 0xc3, 0xca, 0xcd,
	0x90, 0x97, 0x9e, 0x99, 0x8c, 0x8b, 0x82, 0x85, 0xa8, 0xaf, 0xa6, 0xa1,
	0xb4, 0xb3, 0xba, 0xbd, 0xc7, 0xc0, 0xc9, 0xce, 0xdb, 0xdc, 0xd5, 0xd2,
	0xff, 0xf8, 0xf1, 0xf6, 0xe3, 0xe4, 0xed, 0xea, 0xb7, 0xb0, 0xb9, 0xbe,
	0xab, 0xac, 0xa5, 0xa2, 0x8f, 0x88, 0x81, 0x86, 0x93, 0x94, 0x9d, 0x9a,
	0x27, 0x20, 0x29, 0x2e, 0x3b, 0x3c, 0x35, 0x32, 0x1f, 0x18, 0x11, 0x16,
	0x03, 0x04, 0x0d, 0x0a, 0x57, 0x50, 0x59, 0x5e, 0x4b, 0x4c, 0x45, 0x42,
	0x6f, 0x68, 0x61, 0x66, 0x73, 0x74, 0x7d, 0x7a, 0x89, 0x8e, 0x87, 0x80,
	0x95, 0x92, 0x9b, 0x9c, 0xb1, 0xb6, 0xbf, 0xb8, 0xad, 0xaa, 0xa3, 0xa4,
	0xf9, 0xfe, 0xf7, 0xf0, 0xe5, 0xe2, 0xeb, 0xec, 0xc1, 0xc6, 0xcf, 0xc8,
	0xdd, 0xda, 0xd3, 0xd4, 0x69, 0x6e, 0x67, 0x60, 0x75, 0x72, 0x7b, 0x7c,
	0x51, 0x56, 0x5f, 0x58, 0x4d, 0x4a, 0x43, 0x44, 0x19, 0x1e, 0x17, 0x10,
	0x05, 0x02, 0x0b, 0x0c, 0x21, 0x26, 0x2f, 0x28, 0x3d, 0x3a, 0x33, 0x34,
	0x4e, 0x49, 0x40, 0x47, 0x52, 0x55, 0x5c, 0x5b, 0x76, 0x71, 0x78, 0x7f,
	0x6a, 0x6d, 0x64, 0x63, 0x3e, 0x39, 0x30, 0x37, 0x22, 0x25, 0x2c, 0x2b,
	0x06, 0x01, 0x08, 0x0f, 0x1a, 0x1d, 0x14, 0x13, 0xae, 0xa9, 0xa0, 0xa7,
	0xb2, 0xb5, 0xbc, 0xbb, 0x96, 0x91, 0x98, 0x9f, 0x8a, 0x8d, 0x84, 0x83,
	0xde, 0xd9, 0xd0, 0xd7, 0xc2, 0xc5, 0xcc, 0xcb, 0xe6, 0xe1, 0xe8, 0xef,
	0xfa, 0xfd, 0xf4, 0xf3
]

def crc8(data):
	'crc8 checksum'
	crc = 0
	for byte in data:
		crc = crc8_table[(crc ^ byte) & 0xff]
	return crc & 0xff

def reverse_bits(i: int):
	'Reverse the bits of this byte (as `int`)'
	i = ((i & 0b10101010) >> 1) | ((i & 0b01010101) << 1)
	i = ((i & 0b11001100) >> 2) | ((i & 0b00110011) << 2)
	return ((i & 0b11110000) >> 4) | ((i & 0b00001111) << 4)

def int_to_bytes(i: int, length=1, big_endian=False) -> bytes:
	max_value = (1 << (length * 8)) - 1
	if type(i) is not int:
		raise f'int_to_bytes: not int: {i}'
	if i < 0:
		raise f'int_to_bytes: {i} < 0'
	if i > max_value:
		raise f'int_to_bytes: {i} > {max_value}'
	b = bytearray(length)
	p = 0
	while i != 0:
		b[p] = i & 0xff
		i >>= 8
		p += 1
	if big_endian:
		b = reversed(b)
	return bytes(b)


# classes

class Commander(metaclass=ABCMeta):
	''' Semi-abstract class, to be inherited by `PrinterDriver`
		Contains binary data communication interface for individual functions
		"Commander" of kind of printers like GB0X, GT01
		Class structure is not guaranteed to be stable
	'''

	dry_run: bool = False

	data_flow_pause = b'\x51\x78\xae\x01\x01\x00\x10\x70\xff'
	data_flow_resume = b'\x51\x78\xae\x01\x01\x00\x00\x00\xff'

	def make_command(self, command_bit, payload: bytearray, *,
					 prefix=bytearray(), suffix=bytearray()):
		'Make bytes that to be used to control printer'
		payload_size = len(payload)
		if payload_size > 0xff:
			raise ValueError(f'Command payload too big ({payload_size} > 255)')
		return prefix + bytearray(
			[ 0x51, 0x78, command_bit, 0x00, payload_size, 0x00 ]
		) + payload + bytearray( [ crc8(payload), 0xff ] ) + suffix

	def start_printing(self):
		'Start printing'
		self.send( bytearray([0x51, 0x78, 0xa3, 0x00, 0x01, 0x00, 0x00, 0x00, 0xff]) )

	def start_printing_new(self):
		'Start printing on newer printers'
		self.send( bytearray([0x12, 0x51, 0x78, 0xa3, 0x00, 0x01, 0x00, 0x00, 0x00, 0xff]) )

	def apply_energy(self):
		''' Apply previously set energy to printer
		'''
		self.send( self.make_command(0xbe, int_to_bytes(0x01)) )

	def get_device_state(self):
		'(unknown). seems it could refresh device state & apply config'
		self.send( self.make_command(0xa3, int_to_bytes(0x00)) )

	def get_device_info(self):
		'(unknown). seems it could refresh device state & apply config'
		self.send( self.make_command(0xa8, int_to_bytes(0x00)) )

	def update_device(self):
		'(unknown). seems it could refresh device state & apply config'
		self.send( self.make_command(0xa9, int_to_bytes(0x00)) )

	def set_dpi_as_200(self):
		'(unknown)'
		self.send( self.make_command(0xa4, int_to_bytes(50)) )

	def start_lattice(self):
		'Mark the start of printing'
		self.send( self.make_command(0xa6, bytearray(
			[0xaa, 0x55, 0x17, 0x38, 0x44, 0x5f, 0x5f, 0x5f, 0x44, 0x38, 0x2c]
		)) )

	def end_lattice(self):
		'Mark the end of printing'
		self.send( self.make_command(0xa6, bytearray(
			[ 0xaa, 0x55, 0x17, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x17 ]
		)) )

	def retract_paper(self, pixels: int):
		'Retract the paper for some pixels'
		self.send( self.make_command(0xa0, int_to_bytes(pixels, length=2)) )

	def feed_paper(self, pixels: int):
		'Feed the paper for some pixels'
		self.send( self.make_command(0xa1, int_to_bytes(pixels, length=2)) )

	def set_speed(self, value: int):
		''' Set how quick to feed/retract paper. **The lower, the quicker.**
			My printer with value < 4 set would make it unable to feed/retract,
			maybe it's way too quick.
			Speed also affects the quality, for heat time/stability reasons.
		'''
		self.send( self.make_command(0xbd, int_to_bytes(value)) )

	def set_energy(self, amount: int):
		''' Set thermal energy, max to `0xffff`
			By default, it's seems around `0x3000` (1 / 5)
		'''
		self.send( self.make_command(0xaf, int_to_bytes(amount, length=2)) )

	def draw_bitmap(self, bitmap_data: bytearray):
		'Print `bitmap_data`. Also does the bit-reversing job.'
		data = bytearray( map(reverse_bits, bitmap_data) )
		self.send( self.make_command(0xa2, data) )

	def draw_compressed_bitmap(self, bitmap_data: bytearray):
		'TODO. Print `bitmap_data`, compress if worthy so'
		self.draw_bitmap(bitmap_data)

	@abstractmethod
	def send(self, data):
		'Send data to device, or whatever'
		...

class PrinterError(Exception):
	'Exception raised when something went wrong during printing'
	message: str
	def __init__(self, *args):
		super().__init__(*args)
		self.message = args[0]

class ExitCodes():
    'Exit codes'
    Success = 0
    GeneralError = 1
    InvalidArgument = 2
    PrinterError = 64
    IncompleteProgram = 128
    MissingDependency = 129
    UserInterrupt = 254

def info(*args, **kwargs):
    'Just `print` to `stdout`'
    print(*args, **kwargs, file=sys.stdout, flush=True)

def error(*args, exception=None, **kwargs):
    '`print` to `stderr`, or optionally raise an exception'
    if exception is not None:
        raise exception(*args)
    else:
        print(*args, **kwargs, file=sys.stderr, flush=True)

def fatal(*args, code=ExitCodes.GeneralError, **kwargs):
    '`print` to `stderr`, and exit with `code`'
    print(*args, **kwargs, file=sys.stderr, flush=True)
    sys.exit(code)

class PrinterData():
	''' The image data to be used by `PrinterDriver`.
		Optionally give an io `file` to read PBM image data from it.
		To read the bitmap data, simply do `io` operation with attribute `data`
	'''

	buffer = 4 * 1024 * 1024

	width: int
	'Constant width'
	_data_width: int
	'Amount of data bytes per line'
	height: int
	'Total height of bitmap data'
	data: bytearray
	'Monochrome bitmap data `io`, of size `width * height // 8`'
	pages: list
	'Height of every page in a `list`'
	max_size: int
	'Max size of `data`'
	full: bool
	'Whether the data is full (i.e. have reached max size)'

	def __init__(self, width, file: io.BufferedIOBase=None, max_size=64 * 1024 * 1024):
		self.width = width
		self._data_width = width // 8
		self.height = 0
		self.max_size = max_size
		self.max_height = max_size // self._data_width
		self.full = False
		self.data = io.BytesIO()
		self.pages = []
		if file is not None:
			self.from_pbm(file)

	def write(self, data: bytearray):
		''' Directly write bitmap data to `data` directly. For memory safety,
			will overwrite earliest data if going to reach `max_size`.
			returns the io position after writing.
		'''
		data_len = len(data)
		if self.data.tell() + data_len > self.max_size:
			self.full = True
			self.data.seek(0)
		self.data.write(data)
		position = self.data.tell()
		if not self.full:
			self.height = position // self._data_width
		return position

	def read(self, length=-1):
		''' Read the bitmap data entirely, in chunks.
			`yield` the resulting data.
			Will finally put seek point to `0`
		'''
		self.data.seek(0)
		while chunk := self.data.read(length):
			yield chunk
		self.data.seek(0)

	def from_pbm(self, file: io.BufferedIOBase):
		''' Read from buffer `file` that have PBM image data.
			Concatenating multiple files *is* allowed.
			Calling multiple times is also possible,
			before or after yielding `read`, not between.
			Will put seek point to last byte written.
		'''
		while signature := file.readline():
			if signature != b'P4\n':
				error('input-is-not-pbm-image', exception=PrinterError)
			while True:
				# There can be comments. Skip them
				line = file.readline()[0:-1]
				if line[0:1] != b'#':
					break
			width, height = map(int, line.split(b' '))
			if width != self.width:
				error(
					'unsuitable-image-width-expected-0-got-1',
					self.width, width,
					exception=PrinterError
				)
			self.pages.append(height)
			self.height += height
			total_size = 0
			expected_size = self._data_width * height
			while raw_data := file.read(
					min(self.buffer, expected_size - total_size)):
				total_size += len(raw_data)
				self.write(raw_data)
				if self.full:
					self.pages.pop(0)
			if total_size != expected_size:
				error('broken-pbm-image', exception=PrinterError)
		if file is not sys.stdin.buffer:
			file.close()

	def to_pbm(self, *, merge_pages=False):
		''' `yield` the pages as PBM image data,
			optionally just merge to one page.
			Will restore the previous seek point.
		'''
		pointer = self.data.tell()
		self.data.seek(0)
		if merge_pages:
			yield bytearray(
				b'P4\n%i %i\n' % (self.width, self.height)
			) + self.data.read()
		else:
			for i in self.pages:
				yield bytearray(
					b'P4\n%i %i\n' % (self.width, i)
				) + self.data.read(self._data_width * i)
		self.data.seek(pointer)

	def __del__(self):
		self.data.truncate(0)
		self.data.close()
		del self.data

class Model():
    ''' A printer model
        `paper_width`: pixels per line for the model/paper
        `is_new_kind`: some models have new "start print" command and can understand compressed data.
                the algorithm isn't implemented in Cat-Printer yet, but this should be no harm.
        `problem_feeding`: didn't yet figure out MX05/MX06 bad behavior giving feed command, use workaround for them
    '''
    paper_width: int = 384
    is_new_kind: bool = False
    problem_feeding: bool = False

Models = {}

# all known supported models
for name in '_ZZ00 GB01 GB02 GB03 GT01 MX05 MX06 MX08 MX09 MX10 YT01'.split(' '):
    Models[name] = Model()

# that can receive compressed data
for name in 'GB03'.split(' '):
    Models[name].is_new_kind = True

# feed message isn't handled corrently in the codebase, and these models have problems with it
# TODO fix that piece of code
for name in 'MX05 MX06 MX08 MX09 MX10'.split(' '):
    Models[name].problem_feeding = True


class PrinterDriver(Commander):
	'The core driver of Cat-Printer'

	device: BleakClient = None
	'The connected printer device.'

	model: Model = None
	'The printer model'

	scan_time: float = 4.0

	connection_timeout : float = 5.0

	font_family: str = 'font'
	flip_h: bool = False
	flip_v: bool = False
	wrap: bool = False
	rtl: bool = False
	font_scale: int = 1

	energy: int = None
	'Thermal strength of printer, range 0x0000 to 0xffff'
	speed: int = 32

	mtu: int = 200

	tx_characteristic = '0000ae01-0000-1000-8000-00805f9b34fb'
	rx_characteristic = '0000ae02-0000-1000-8000-00805f9b34fb'

	dry_run: bool = False
	'Test print process only, will not waste paper'

	fake: bool = False
	'Test data logic only, will not waste time'

	dump: bool = False
	'Dump traffic data, and if it\'s text printing, the resulting PBM image'

	_loop: asyncio.AbstractEventLoop = None

	_traffic_dump: io.FileIO = None

	_paused: bool = False

	_pending_data: io.BytesIO = None

	def __init__(self):
		self._loop = asyncio.get_event_loop_policy().new_event_loop()

	def loop(self, *futures):
		''' Run coroutines in order in current event loop until complete,
			return its result directly, or their result as tuple.

			This 1) ensures exiting gracefully (futures always get completed before exiting),
			and 2) avoids function colors (use of "await", especially outside this script)
		'''
		results = []
		for future in futures:
			results.append(self._loop.run_until_complete(future))
		return results[0] if len(results) == 1 else tuple(results)

	def connect(self, name=None, address=None):
		''' Connect to this device, and operate on it
		'''
		self._pending_data = io.BytesIO()
		if self.fake:
			return
		if (self.device is not None and address is not None and
			(self.device.address.lower() == address.lower())):
			return
		try:
			if self.device is not None and self.device.is_connected:
				self.loop(self.device.stop_notify(self.rx_characteristic))
				self.loop(self.device.disconnect())
		except:     # pylint: disable=bare-except
			pass
		finally:
			self.device = None
		if name is None and address is None:
			return
		self.model = Models.get(name, Models['_ZZ00'])
		self.device = BleakClient(address)
		def notify(_char, data):
			if data == self.data_flow_pause:
				self._paused = True
			elif data == self.data_flow_resume:
				self._paused = False
		self.loop(
			self.device.connect(timeout=self.connection_timeout),
			self.device.start_notify(self.rx_characteristic, notify)
		)

	def scan(self, identifier: str=None, *, use_result=False, everything=False):
		''' Scan for supported devices, optionally filter with `identifier`,
			which can be device model (bluetooth name), and optionally MAC address, after a comma.
			If `use_result` is True, connect to the first available device to driver instantly.
			If `everything` is True, return all bluetooth devices found.
			Note: MAC address doesn't work on Apple MacOS. In place with it,
			You need an UUID of BLE device dynamically given by MacOS.
		'''
		if self.fake:
			return []
		if everything:
			devices = self.loop(BleakScanner.discover(self.scan_time))
			return devices
		if identifier:
			if identifier.find(',') != -1:
				name, address = identifier.split(',')
				if name not in Models:
					error('model-0-is-not-supported-yet', name, exception=PrinterError)
				# TODO: is this logic correct?
				if address[2::3] != ':::::' and len(address.replace('-', '')) != 32:
					error('invalid-address-0', address, exception=PrinterError)
				if use_result:
					self.connect(name, address)
				return [BLEDevice(address, name)]
			if (identifier not in Models and
				identifier[2::3] != ':::::' and len(identifier.replace('-', '')) != 32):
				error('model-0-is-not-supported-yet', identifier, exception=PrinterError)
		# scanner = BleakScanner()
		devices = [x for x in self.loop(
			BleakScanner.discover(self.scan_time)
		) if x.name in Models]
		if identifier:
			if identifier in Models:
				devices = [dev for dev in devices if dev.name == identifier]
			else:
				devices = [dev for dev in devices if dev.address.lower() == identifier.lower()]
		if use_result and len(devices) != 0:
			self.connect(devices[0].name, devices[0].address)
		return devices

	def print(self, file: io.BufferedIOBase, *, mode='default',
			  identifier: str=None):
		''' Print data of `file`.
			Currently, available modes are `pbm` and `text`.
			If no devices were connected, scan & connect to one first.
		'''
		self._pending_data = io.BytesIO()
		if self.device is None:
			self.scan(identifier, use_result=True)
		if self.device is None and not self.fake:
			error('no-available-devices-found', exception=PrinterError)
		if mode in ('pbm', 'default'):
			printer_data = PrinterData(self.model.paper_width, file)
			self._print_bitmap(printer_data)
		else:
			... # TODO: other?

	def flush(self):
		'Send pending data instantly, but will block if paused'
		self._pending_data.seek(0)
		while chunk := self._pending_data.read(self.mtu):
			while self._paused:
				self.loop(asyncio.sleep(0.2))
			self.loop(
				self.device.write_gatt_char(self.tx_characteristic, chunk),
				asyncio.sleep(0.02)
			)
		self._pending_data.seek(0)
		self._pending_data.truncate()

	def send(self, data):
		''' Pend `data`, send if enough size is reached.
			You can manually `flush` to send data instantly,
			and should do `flush` at the end of printing.
		'''
		if self.dump:
			if self._traffic_dump is None:
				self._traffic_dump = open('traffic.dump', 'wb')
			self._traffic_dump.write(data)
		if self.fake:
			return
		self._pending_data.write(data)
		if self._pending_data.tell() > self.mtu * 16 and not self._paused:
			self.flush()

	def _prepare(self):
		self.get_device_state()
		if self.model.is_new_kind:
			self.start_printing_new()
		else:
			self.start_printing()
		self.set_dpi_as_200()
		if self.speed:    # well, slower makes stable heating
			self.set_speed(self.speed)
		if self.energy is not None:
			self.set_energy(self.energy)
		self.apply_energy()
		self.update_device()
		self.flush()
		self.start_lattice()

	def _finish(self):
		self.end_lattice()
		self.set_speed(8)
		if self.model.problem_feeding:
			for _ in range(128):
				self.draw_bitmap(bytes(self.model.paper_width // 8))
		else:
			self.feed_paper(128)
		self.get_device_state()
		self.flush()

	def _print_bitmap(self, data: PrinterData):
		paper_width = self.model.paper_width
		flip(data.data, data.width, data.height, self.flip_h, self.flip_v, overwrite=True)
		self._prepare()
		# TODO: consider compression on new devices
		for chunk in data.read(paper_width // 8):
			if self.dry_run:
				chunk = b'\x00' * len(chunk)
			self.draw_bitmap(chunk)
		if self.dump:
			with open('dump.pbm', 'wb') as dump_pbm:
				dump_pbm.write(next(data.to_pbm(merge_pages=True)))
		self._finish()

	def _get_pf2(self, path: str):
		''' Get file io of a PF2 font in several ways
		'''
		path += '.pf2'
		file = None
		parents = ('', 'pf2/')
		if not path:
			path = 'unifont'
		for parent in parents:
			if os.path.exists(full_path := os.path.join(parent, path)):
				file = open(full_path, 'rb')
				break
		else: # if didn't break
			if os.path.exists('pf2.zip'):
				with zipfile.ZipFile('pf2.zip') as pf2zip:
					for name in pf2zip.namelist():
						if name == path:
							with pf2zip.open(name) as f:
								file = io.BytesIO(f.read())
							break
		return file

	def unload(self):
		''' Unload this instance, disconnect device and clean up.
		'''
		if self.device is not None:
			info('disconnecting from printer')
			try:
				self.loop(
					self.device.stop_notify(self.rx_characteristic),
					self.device.disconnect()
				)
			except (BleakError, EOFError):
				self.device = None
		if self._traffic_dump is not None:
			self._traffic_dump.close()
		self._loop.close()

__all__ = (PrinterDriver, Models)