# -*- coding: utf-8 -*-
import base64

import struct

from pymax.objects import ProgramSchedule, RFAddr
from pymax.util import Debugger, unpack_temp_and_time
import datetime
import logging

logger = logging.getLogger(__file__)

HELLO_RESPONSE = 'H'
M_RESPONSE = 'M'
CONFIGURATION_RESPONSE = 'C'
L_RESPONSE = 'L'
F_RESPONSE = 'F'
SET_RESPONSE = 'S'

MultiPartResponses = M_RESPONSE,

DeviceCube = 0
DeviceRadiatorThermostat = 1
DeviceRadiatorThermostatPlus = 2
DeviceWallThermostat = 3
DeviceShutterContact = 4
DeviceEcoButton = 5

def device_type_name(device_type):
	device_type_names = (
		'Cube', 'Thermostat', 'Thermostat Plus', 'Wall Thermostat', 'Shutter contact', 'Eco button'
	)
	if device_type < len(device_type_names):
		return device_type_names[device_type]
	return None


class BaseResponse(Debugger):
	length = None
	min_length = None
	max_length = None

	def __init__(self, response):
		if not response:
			raise ValueError("No data given")

		if self.length is not None and len(response) != self.length:
			raise ValueError("Byte array must be %s bytes in length (is %s)" % (self.length, len(response)))

		if self.min_length is not None and len(response) < self.min_length:
			raise ValueError("Byte array must be at least %s bytes in length (is %s)" % (self.length, len(response)))

		if self.max_length is not None and len(response) > self.max_length:
			raise ValueError("Byte array must be at most %s bytes in length (is %s)" % (self.length, len(response)))

		self.raw_response = response
		self.dump_bytes(response)
		self._parse()

	@property
	def data(self):
		return self.raw_response

	def _parse(self):
		raise NotImplementedError

	def bytes_to_int(self, barray):
		if barray is None or len(barray) == 0:
			return None
		self.dump_bytes(barray, "Bytes to int")
		return sum(struct.unpack('b' * len(barray), barray))


class MultiResponse(BaseResponse):

	def __init__(self, response):
		super(MultiResponse, self).__init__([response] if isinstance(response, bytearray) else response)

	@property
	def data(self):
		raise NotImplementedError


class DiscoveryIdentifyResponse(BaseResponse):
	length = 26

	def _parse(self):
		self.name = self.data[0:8].decode('utf-8')
		self.serial = self.data[8:18].decode('utf-8')
		self.request_id = chr(self.data[18])
		self.request_type = chr(self.data[19])
		self.rf_address = RFAddr(self.data[21:24])
		self.fw_version = ''.join("%02x" % x for x in self.data[24:26])

	def __str__(self):
		return "%s: RF addr: %s, FW version: %s" % (self.serial, self.rf_address, self.fw_version)

	def __eq__(self, other):
		return isinstance(other, DiscoveryIdentifyResponse) and \
				self.name == other.name and \
				self.serial == other.serial and \
				self.request_id == other.request_id and \
				self.request_type == other.request_type and \
				self.rf_address == other.rf_address and \
				self.fw_version == other.fw_version


class DiscoveryNetworkConfigurationResponse(BaseResponse):
	length = 40

	def _parse(self):
		self.name = self.data[0:8].decode('utf-8')
		self.serial = self.data[8:18].decode('utf-8')
		self.request_id = chr(self.data[18])
		self.request_type = chr(self.data[19])
		self.ip_address = '.'.join([str(x) for x in self.data[20:24]])
		self.gateway = '.'.join([str(x) for x in self.data[24:28]])
		self.netmask = '.'.join([str(x) for x in self.data[28:32]])
		self.dns1 = '.'.join([str(x) for x in self.data[32:36]])
		self.dns2 = '.'.join([str(x) for x in self.data[36:40]])

	def __str__(self):
		return "%s: IP: %s, Netmask: %s, Gateway: %s, DNS1: %s, DNS2: %s" % (self.serial, self.ip_address, self.netmask, self.gateway, self.dns1, self.dns2)

	def __eq__(self, other):
		return isinstance(other, DiscoveryNetworkConfigurationResponse) and \
				self.name == other.name and \
				self.serial == other.serial and \
				self.request_id == other.request_id and \
				self.request_type == other.request_type and \
				self.ip_address == other.ip_address and \
				self.gateway == other.gateway and \
				self.netmask == other.netmask and \
				self.dns1 == other.dns1 and \
				self.dns2 == other.dns2


class HelloResponse(BaseResponse):
	length = 66

	def _parse(self):
		parts = tuple(self.data.split(b','))
		self.serial = parts[0].decode('utf-8')
		self.rf_address = RFAddr(parts[1].decode('utf-8'))
		self.fw_version = parts[2].decode('utf-8')
		# unknown = parts[3]
		self.http_connection_id = parts[4]
		self.duty_cycle = parts[5]
		self.free_mem_slots = parts[6]
		date = parts[7]
		time = parts[8]
		self.state_cube_time = parts[9]
		self.ntp_counter = parts[10]

		# 0f0c0c -> 2015-12-12
		self.datetime = datetime.datetime(int(date[0:2].decode('utf-8'), 16) + 2000,
										  int(date[2:4].decode('utf-8'), 16),
										  int(date[4:6].decode('utf-8'), 16),
										  int(time[0:2].decode('utf-8'), 16),
										  int(time[2:4].decode('utf-8'), 16))

	def __str__(self):
		return "%s: RF addr: %s, FW: %s, Date: %s" % (self.serial, self.rf_address, self.fw_version, self.datetime)


class MResponse(MultiResponse):

	@property
	def data(self):
		chunks = []

		for part in self.raw_response:
			idx = int(part[0:2].decode('utf-8'))
			chunks.append((idx, part[6:]))

		full_data = bytearray([])
		for _, data in sorted(chunks):
			full_data += data
		return full_data

	def _parse(self):
		base64_data = self.data.decode('utf-8')
		data = bytearray(base64.b64decode(base64_data))

		self.dump_bytes(data, "MResponse")

		# first two bytes are currently unknown
		self.num_rooms = data[2]
		logger.debug("Number of rooms from MResponse: %s", self.num_rooms)
		self.rooms = []
		pos = 3
		for i in range(0, self.num_rooms):
			logger.debug("Parsing room %s of %s (from pos %s)", i + 1, self.num_rooms, pos)

			room_id, name_length = struct.unpack('bb', data[pos:pos+2])
			room_name = data[pos + 2:pos + 2 + name_length].decode('utf-8')
			group_rf_address = RFAddr(data[pos+name_length + 2 : pos+name_length + 2 + 3])
			logger.debug("Room ID: %s, Room Name: %s, Group RF address: %s", room_id, room_name, group_rf_address)
			self.rooms.append((room_id, room_name, group_rf_address))
			# set pos to start of next section
			pos += 1 + 1 + name_length + 3

		self.devices = []

		self.num_devices = data[pos]
		pos += 1

		for device_idx in range(0, self.num_devices):
			device_type = data[pos]
			device_rf_address = RFAddr(data[pos+1 : pos+1 + 3])
			device_serial = data[pos+4:pos+14].decode('utf-8')
			device_name_length = data[pos+14]
			device_name = data[pos+15:pos+15+device_name_length].decode('utf-8')
			room_id = data[pos+15+device_name_length]

			logger.debug("Device: %s, Device RF address: %s, Device serial: %s, Device: %s, Room: %s", device_idx, device_rf_address, device_serial, device_name, room_id)
			self.devices.append((device_idx, device_type, device_rf_address, device_serial, device_name, room_id))

			pos += 1 + 3 + 10 + device_name_length + 2

	def __str__(self):
		return "MResponse (%s rooms, %s devices)" % (self.num_rooms, self.num_devices)


class ConfigurationResponse(BaseResponse):

	def _parse(self):
		device = self.data[:6].decode('utf-8')

		b64 = self.data[7:]
		data = bytearray(base64.b64decode(b64))
		#self.dump_bytes(data, "device config")

		data_length = data[0]
		logger.debug("Data length for device config: %s", data_length)

		self.device_addr = RFAddr(data[1:4])
		self.device_type, self.room_id, self.firmware_version, self.test_result = struct.unpack('bbbb', data[4:8])
		self.serial_number = data[8:17].decode('utf-8')

		logger.debug("Device config for %s: type: %s, room: %s, firmware: %s, test: %s, serial number: %s",
			self.device_addr, self.device_type, self.room_id, self.firmware_version, self.test_result, self.serial_number
		)

		if self.device_type == DeviceCube:
			self._parse_cube_config(data[18:])
		elif self.device_type == DeviceRadiatorThermostat or self.device_type == DeviceRadiatorThermostatPlus:
			self._parse_thermostat_config(data[18:])
		elif self.device_type == DeviceWallThermostat:
			self._parse_wall_thermostat_config(data[18:])
		else:
			logger.warning("Cannot parse device configuration for type %s (%s)", self.device_type, device_type_name(self.device_type))

	def _parse_cube_config(self, config):
		# Position   Length   Information
		# ===================================================
		# 0012       1        Is Portal Enabled
		# 0013-0054  66       Unknown
		# 0055-????  ??       Portal URL
		# ????-00ed  ??       Unknown
		self.portal_enabled = bool(config[11])
		end_of_url = config.index(b'\0', 67)
		self.portal_url = config[67:end_of_url].decode('utf-8')

	def _parse_thermostat_config(self, config):
		# Pos  Len  Information
		# ================================================================
		# 12   1    Comfort Temperature       in degrees celsius * 2
		# 13   1    Eco Temperature           in degrees celsius * 2
		# 14   1    Max Set Point Temperature in degrees celsius * 2
		# 15   1    Min Set Point Temperature in degrees celsius * 2
		# 16   1    Temperature offset        in degrees celsius * 2 + 3,5
		# 17   1    Window Open Temperature   in degrees celsius * 2
		# 18   1    Window Open Duration      in minutes * 5
		# 19   1    Boost                     3 MSB bits are duration:
		#                                       value is in minutes * 5
		#                                       but value 7 means 60 min.
		#                                     5 LSB bits are valve opening
		#                                       in % * 5
		# 1a   1    Decalcification           3 MSB bits are day of week:
		#                                       Saturday = 0 etc.
		#                                     5 LSB bits are time in hours
		# 1b   1    Max Valve Setting         in % * 255 / 100  (so to get
		#                                       valve setting use
		#                                       value * 100 / 255)
		# 1c   1    Valve Offset              in % * 255 / 100
		# 1d   182  Weekly Program            Schedule of 26 bytes for
		#                                     each day starting with
		#                                     Saturday. Each schedule
		#                                     consists of 13 words
		#                                     (2 bytes) e.g. set points.
		#                                     1 set point consist of
		#                                     7 MSB bits is temperature
		#                                       set point (in degrees * 2)
		#                                     9 LSB bits is until time
		#                                       (in minutes * 5)

		self.comfort_temperature_raw, \
		self.eco_temperature_raw,\
		self.max_set_point_temperature_raw,\
		self.min_set_point_temperature_raw,\
		self.temperature_offset_raw, \
		self.window_open_temperature_raw,\
		self.window_open_duration_raw, \
		self.boost_raw,\
		self.decalcification_raw,\
		self.max_valve_raw,\
		self.valve_offset_raw = struct.unpack('BBBBBBBBBBB', config[:11])

		ConfigurationResponse.comfort_temperature = property(lambda x: x.comfort_temperature_raw / 2.0)
		ConfigurationResponse.eco_temperature = property(lambda x: x.eco_temperature_raw / 2.0)
		ConfigurationResponse.max_set_point_temperature = property(lambda x: x.max_set_point_temperature_raw / 2.0)
		ConfigurationResponse.min_set_point_temperature = property(lambda x: x.min_set_point_temperature_raw / 2.0)
		ConfigurationResponse.temperature_offset = property(lambda x: (x.temperature_offset_raw / 2.0) - 3.5)
		ConfigurationResponse.window_open_temperature = property(lambda x: x.window_open_temperature_raw / 2.0)
		ConfigurationResponse.window_open_duration = property(lambda x: x.window_open_duration_raw * 5.0)
		ConfigurationResponse.boost_duration = property(lambda x: (x.boost_raw >> 5) * 5 if x.boost_raw >> 5 < 7 else 60)
		ConfigurationResponse.boost_valve_setting = property(lambda x: int(x.boost_raw - (x.boost_raw >> 5 << 5)) * 5)

		ConfigurationResponse.decalcification_day = property(lambda x: x.decalcification_raw >> 5)
		ConfigurationResponse.decalcification_hour = property(lambda x: int(x.decalcification_raw - (x.decalcification_raw >> 5 << 5)))

		ConfigurationResponse.max_valve_setting = property(lambda x: x.max_valve_raw * 100 / 255)

		logger.debug("Comfort temperature:       %s°C (raw: %s)", self.comfort_temperature, self.comfort_temperature_raw)
		logger.debug("Eco temperature:           %s°C (raw: %s)", self.eco_temperature, self.eco_temperature_raw)
		logger.debug("Max set point temperature: %s°C (raw: %s)", self.max_set_point_temperature, self.max_set_point_temperature_raw)
		logger.debug("Min set point temperature: %s°C (raw: %s)", self.min_set_point_temperature, self.min_set_point_temperature_raw)
		logger.debug("Temperature offset:        %s°C (raw: %s)", self.temperature_offset, self.temperature_offset_raw)
		logger.debug("Window open temperature:   %s°C (raw: %s)", self.window_open_temperature, self.window_open_temperature_raw)
		logger.debug("Window open duration:      %s min (raw: %s)", self.window_open_duration, self.window_open_duration_raw)
		logger.debug("Boost:                     %s minutes, %s %%", self.boost_duration, self.boost_valve_setting)
		logger.debug("Decalcification:           day %s, hour %s", self.decalcification_day, self.decalcification_hour)
		logger.debug("Max valve setting:         %s%% (raw: %s)", self.max_valve_setting, self.max_valve_raw)
		self.week_program = self._parse_week_program(config[11:])

	def _parse_week_program(self, buffer):
		program = []

		for day in range(0, 7):
			day_schedules = []
			offset = day * 26

			day_config = buffer[offset:offset+26]

			start = datetime.time()

			for schedule_offset in range(0, 26, 2):
				schedule_bytes = day_config[schedule_offset:schedule_offset+2]
				temp, time = unpack_temp_and_time(schedule_bytes)

				schedule = ProgramSchedule(temp, start, time)
				day_schedules.append(schedule)

				start = schedule.end_minutes

				if time >= 1440:
					break

			program.append(day_schedules)

		return program

	def _parse_wall_thermostat_config(self, buffer):
		# Pos  Len  Information
		# ================================================================
		# 12   1    Comfort Temperature       in degrees celsius * 2
		# 13   1    Eco Temperature           in degrees celsius * 2
		# 14   1    Max Set Point Temperature in degrees celsius * 2
		# 15   1    Min Set Point Temperature in degrees celsius * 2
		# 1d   182  Weekly Program            Schedule of 26 bytes for
		#                                     each day starting with
		#                                     Saturday. Each schedule
		#                                     consists of 13 words
		#                                     (2 bytes) e.g. set points.
		#                                     1 set point consist of
		#                                     7 MSB bits is temperature
		#                                       set point (in degrees * 2)
		#                                     9 LSB bits is until time
		#                                       (in minutes * 5)
		# cc   3    Unknown
		self.comfort_temperature_raw, \
		self.eco_temperature_raw,\
		self.max_set_point_temperature_raw,\
		self.min_set_point_temperature_raw = struct.unpack('BBBB', buffer[:4])

		ConfigurationResponse.comfort_temperature = property(lambda x: x.comfort_temperature_raw / 2.0)
		ConfigurationResponse.eco_temperature = property(lambda x: x.eco_temperature_raw / 2.0)
		ConfigurationResponse.max_set_point_temperature = property(lambda x: x.max_set_point_temperature_raw / 2.0)
		ConfigurationResponse.min_set_point_temperature = property(lambda x: x.min_set_point_temperature_raw / 2.0)
		self.week_program = self._parse_week_program(buffer[5:])


	def __str__(self):
		s = "%s config: serial %s, address: %s" % (device_type_name(self.device_type), self.serial_number, self.device_addr)

		if self.device_type == DeviceCube:
			s += ", portal enabled: %s, portal url: %s" % (self.portal_enabled, self.portal_url)

		return s


class LResponse(BaseResponse):

	def _parse(self):
		data = bytearray(base64.b64decode(self.data))
		submessage_len, rf1, rf2, rf3, unknown, flags1, flags2 = struct.unpack('B3BBBB', bytearray(data[:7]))
		self.rf_addr = RFAddr((rf1, rf2, rf3))

		self.weekly_program = not (flags2 & 0x01 or flags2 & 0x02)
		self.manual_program = bool(flags2 & 0x01 and not flags2 & 0x02)
		self.vacation_program = bool(flags2 & 0x02 and not flags2 & 0x01)
		self.boost_program = bool(flags2 & 0x01 and flags2 & 0x02)
		self.dst_active = flags2 & 0x08

		self.gateway_known = bool(flags2 & 0x05)
		self.panel_locked = bool(flags2 & 0x06)
		self.link_ok = bool(flags2 & 0x07)
		self.battery_low = bool(not (flags2 & 0x08))

		self.status_initialized = bool(flags1 & 0x02)
		self.is_answer = bool(not (flags1 & 0x03))
		self.is_error = bool(flags1 & 0x04)
		self.is_valid = bool(flags1 & 0x05)

		if submessage_len > 6:
			self._parse_extra_fields(data)

	def _parse_extra_fields(self, data):
		self.valve_position, self.temperature, du1, du2, time_until = struct.unpack('5B', data[7:12])
		self.time_until = datetime.timedelta(minutes=time_until * 30)
		self.temperature /= 2.0

	def __str__(self):
		return "%s: RF addr: %s, program: (weekly: %s, manual: %s, vacation: %s, boost_program: %s)" % (
			self.__class__.__name__,
			self.rf_addr, self.weekly_program, self.manual_program, self.vacation_program, self.boost_program
		)


class FResponse(BaseResponse):
	def _parse(self):
		self.ntp_servers = self.data.decode('utf-8').split(',')

	def __str__(self):
		return "NTP Servers: %s" % ', '.join(self.ntp_servers)

	def __eq__(self, other):
		return isinstance(other, FResponse) and self.ntp_servers == other.ntp_servers


class SetResponse(BaseResponse):

	def _parse(self):
		self.duty_cycle, self.command_result, self.free_mem_slots = self.data.decode('utf-8').split(',')
		self.duty_cycle = int(self.duty_cycle, 16)
		self.free_mem_slots = int(self.free_mem_slots, 16)
		self.command_result = int(self.command_result)
		self.command_success = self.command_result == 0

	def __str__(self):
		return "SetResponse: Command success: %s" % self.command_success