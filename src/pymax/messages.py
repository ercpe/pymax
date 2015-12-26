# -*- coding: utf-8 -*-
import base64

import struct

from pymax.objects import ProgramSchedule
from pymax.util import date_to_dateuntil, py_day_to_cube_day, pack_temp_and_time, Debugger, unpack_temp_and_time

QUIT_MESSAGE = 'q'
F_MESSAGE = 'f'
S_MESSAGE = 's'

class BaseMessage(object):

	base64payload = False

	def __init__(self, msg):
		self.msg = msg

	def to_bytes(self):
		data = (self.msg + ':').encode('utf-8')

		payload = self.get_payload()
		if payload:
			if self.base64payload:
				data += base64.b64encode(payload)
			else:
				data += payload

		data += bytearray(b"\r\n")
		return data

	def get_payload(self):
		return None


class QuitMessage(BaseMessage):

	def __init__(self):
		super(QuitMessage, self).__init__(QUIT_MESSAGE)


class FMessage(BaseMessage):
	def __init__(self, ntp_servers=None):
		super(FMessage, self).__init__(F_MESSAGE)
		self.ntp_servers = ntp_servers

	def get_payload(self):
		s = ','.join((x.strip() for x in self.ntp_servers or []))
		return bytearray(s, 'utf-8')

	def __eq__(self, other):
		return isinstance(other, FMessage) and self.ntp_servers == other.ntp_servers


class SetMessage(BaseMessage):
	base64payload = True

	TemperatureAndMode = 0x440000000
	Program = 0x410000000
	Temperatures = 0x11000000
	ValveConfig = 0x0412000000

	def __init__(self, type, rf_addr, room_number):
		super(SetMessage, self).__init__(S_MESSAGE)
		self.rf_addr = rf_addr
		self.type = type
		self.room_number = room_number

	def get_payload(self):
		return bytearray(struct.pack('!Q', self.type)[-6:]) + bytearray([
			int(self.rf_addr[0:2], 16),
			int(self.rf_addr[2:4], 16),
			int(self.rf_addr[4:6], 16)
		]) + bytearray([self.room_number])

	def __eq__(self, other):
		return isinstance(other, SetMessage) and self.rf_addr == other.rf_addr and self.type == other.type and \
			self.room_number == other.room_number


class SetTemperatureAndModeMessage(SetMessage):
	ModeAuto = 0x0
	ModeManual = 0x40
	ModeVacation = 0x80
	ModeBoost = 0xc0

	def __init__(self, rf_addr, room_number, mode, **kwargs):
		super(SetTemperatureAndModeMessage, self).__init__(SetMessage.TemperatureAndMode, rf_addr, room_number)
		self.mode = mode
		self.temperature = kwargs.get('temperature', 0)
		self.end = kwargs.get('end', None)

	def get_payload(self):
		x = int(self.temperature * 2)
		x |= self.mode

		payload = super(SetTemperatureAndModeMessage, self).get_payload() + bytearray([x])

		if self.end:
			payload += date_to_dateuntil(self.end.date())
			payload += bytearray([(self.end.time().hour * 2) + (1 if self.end.time().minute >= 30 else 0)])

		return payload

	def __str__(self):
		return "%s(mode=%s, temperature=%s, end=%s)" % (self.__class__.__name__, self.mode, self.temperature, self.end)

	def __repr__(self):
		return self.__str__()

	def __eq__(self, other):
		return super(SetTemperatureAndModeMessage, self).__eq__(other) and \
				isinstance(other, SetTemperatureAndModeMessage) and \
				self.mode == other.mode and \
				self.temperature == other.temperature and \
				self.end == other.end


class SetProgramMessage(SetMessage, Debugger):

	def __init__(self, rf_addr, room_number, weekday, program):
		super(SetProgramMessage, self).__init__(SetMessage.Program, rf_addr, room_number)
		self.weekday = weekday
		self.program = program or []

		if len(self.program) > 13:
			raise ValueError("Program message cannot contain more than 13 schedules per day")

		if not all((isinstance(x, ProgramSchedule) for x in self.program)):
			raise ValueError("Program message takes only ProgramSchedule instances")

	def get_payload(self):
		data = super(SetProgramMessage, self).get_payload()
		data += bytearray([py_day_to_cube_day(self.weekday)])

		# the cube happily accepts less than 13 * 2 bytes for the schedules on a day
		# and will replace the the rest with "low temperature till midnight" schedules
		for schedule in self.program:
			result = pack_temp_and_time(schedule.temperature, schedule.end_minutes)
			rev_temp, rev_minutes = unpack_temp_and_time(result)
			#print("{0}°C, {1} results in {2:2X} {3:2X} ({2:08b} {3:08b}), revd: {4}°C, {5} minutes ({6} h)".format(schedule.temperature, schedule.end_minutes, result[0], result[1], rev_temp, rev_minutes, rev_minutes / 60.0))
			data += result

		self.dump_bytes(data, "SetProgramMessage payload")

		return data

	def __eq__(self, other):
		return super(SetProgramMessage, self).__eq__(other) and isinstance(other, SetProgramMessage) and self.weekday == other.weekday and self.program == other.program


class SetTemperaturesMessage(SetMessage):
	def __init__(self, rf_addr, room_number, comfort, eco, min, max, offset, window_open, window_open_duration):
		super(SetTemperaturesMessage, self).__init__(SetMessage.Temperatures, rf_addr, room_number)
		self.comfort_temperature = comfort
		self.eco_temperature = eco
		self.min_temperature = min
		self.max_temperature = max
		self.temperature_offset = offset
		self.window_open_temperature = window_open
		self.window_open_duration = window_open_duration

	def get_payload(self):
		return super(SetTemperaturesMessage, self).get_payload() + \
			bytearray([
				int(self.comfort_temperature * 2),
				int(self.eco_temperature * 2),
				int(self.max_temperature * 2),
				int(self.min_temperature * 2),
				int((self.temperature_offset + 3.5) * 2),
				int(self.window_open_temperature * 2),
				int(self.window_open_duration / 5)
			])

	def __eq__(self, other):
		return super(SetTemperaturesMessage, self).__eq__(other) and isinstance(other, SetTemperaturesMessage) and \
			self.comfort_temperature == other.comfort_temperature and \
			self.eco_temperature == other.eco_temperature and \
			self.min_temperature == other.min_temperature and \
			self.max_temperature == other.max_temperature and \
			self.temperature_offset == other.temperature_offset and \
			self.window_open_temperature == other.window_open_temperature and \
			self.window_open_duration == other.window_open_duration


class SetValveConfigMessage(SetMessage):

	def __init__(self, rf_addr, room_number, boost_duration, boost_valve_position, decalc_day, decalc_hour, max_valve_setting):
		super(SetValveConfigMessage, self).__init__(SetMessage.ValveConfig, rf_addr, room_number)
		self.boost_duration = boost_duration
		self.boost_valve_position = boost_valve_position / 100.0 if isinstance(boost_valve_position, int) else boost_valve_position
		self.decalc_day = py_day_to_cube_day(decalc_day)
		self.decalc_hour = decalc_hour
		self.max_valve_setting = max_valve_setting

	def get_payload(self):
		boost = int(self.boost_valve_position * 20) | (int(self.boost_duration / 5) << 5)
		decalc = self.decalc_hour | (self.decalc_day << 5)
		max_valve = int((self.max_valve_setting * 255) / 100.0)

		return super(SetValveConfigMessage, self).get_payload() + bytearray([
			boost, decalc, max_valve, 0x00
		])

	def __eq__(self, other):
		return super(SetValveConfigMessage, self).__eq__(other) and \
			isinstance(other, SetValveConfigMessage) and \
			self.boost_duration == other.boost_duration and \
			self.boost_valve_position == other.boost_valve_position and \
			self.decalc_day == other.decalc_day and \
			self.decalc_hour == other.decalc_hour
