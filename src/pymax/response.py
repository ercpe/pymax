# -*- coding: utf-8 -*-
import base64

import struct

from pymax.util import Debugger
import datetime
import logging

logger = logging.getLogger(__file__)

HELLO_RESPONSE = 'H'
M_RESPONSE = 'M'

MultiPartResponses = M_RESPONSE,

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

		#self.data = response
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
		self.rf_address = ''.join("%02x" % x for x in self.data[21:24])
		self.fw_version = ''.join("%02x" % x for x in self.data[24:26])

	def __str__(self):
		return "%s: RF addr: %s, FW version: %s" % (self.serial, self.rf_address, self.fw_version)


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


class HelloResponse(BaseResponse):
	length = 68

	def _parse(self):
		parts = tuple(self.data[2:].split(b','))
		self.serial = parts[0].decode('utf-8')
		self.rf_address = parts[1].decode('utf-8')
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


class MResponse(BaseResponse):

	@property
	def data(self):
		chunks = []

		for part in self.raw_response:
			idx = int(part[2:4].decode('utf-8'))
			chunks.append((idx, part[8:]))

		full_data = bytearray([])
		for _, data in sorted(chunks):
			full_data += data
		return full_data

	def _parse(self):
		base64_data = self.data.decode('utf-8')
		data = bytearray(base64.b64decode(base64_data))

		self.dump_bytes(data, "Base64 decoded")

		# first two bytes are currently unknown
		self.num_rooms = data[2]
		self.rooms = []
		pos = 3
		for _ in range(0, self.num_rooms):
			room_id, name_length = struct.unpack('bb', data[pos:pos+2])
			room_name = data[pos + 2:pos + 2 + name_length].decode('utf-8')
			group_rf_address = ''.join("%X" % x for x in data[pos+name_length + 2 : pos+name_length + 2 + 3])
			logger.debug("Room ID: %s, Room Name: %s, Group RF address: %s" % (room_id, room_name, group_rf_address))
			self.rooms.append((room_id, room_name, group_rf_address))
			# set pos to start of next section
			pos += 1 + 1 + name_length + 3

		self.devices = []

		self.num_devices = data[pos]
		pos += 1

		logging.debug("Devices: %s" % self.num_devices)
		for device_idx in range(0, self.num_devices):
			device_type = data[pos]
			device_rf_address = ''.join("%X" % x for x in data[pos+1 : pos+1 + 3])
			device_serial = data[pos+4:pos+14].decode('utf-8')
			device_name_length = data[pos+14]
			device_name = data[pos+15:pos+15+device_name_length].decode('utf-8')
			room_id = data[pos+15+device_name_length]

			logger.debug("Device: %s, Device RF address: %s, Device serial: %s, Device: %s, Room: %s" % (device_idx, device_rf_address, device_serial, device_name, room_id))
			self.devices.append((device_idx, device_type, device_rf_address, device_serial, device_name, room_id))

			pos += 1 + 3 + 10 + device_name_length + 2

	def __str__(self):
		return "MResponse (%s rooms, %s devices)" % (self.num_rooms, self.num_devices)