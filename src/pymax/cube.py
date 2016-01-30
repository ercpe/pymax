# -*- coding: utf-8 -*-
import socket

import logging

import collections

from pymax.messages import QuitMessage, FMessage, SetTemperatureAndModeMessage, SetProgramMessage, \
	SetTemperaturesMessage, SetValveConfigMessage
from pymax.objects import DeviceList, Device, RFAddr
from pymax.response import DiscoveryIdentifyResponse, DiscoveryNetworkConfigurationResponse, HelloResponse, MResponse, \
	HELLO_RESPONSE, M_RESPONSE, MultiPartResponses, CONFIGURATION_RESPONSE, ConfigurationResponse, L_RESPONSE, LResponse, \
	F_RESPONSE, FResponse, SET_RESPONSE, SetResponse
from pymax.util import Debugger

logger = logging.getLogger(__name__)

Room = collections.namedtuple('Room', ('room_id', 'name', 'rf_address', 'devices'))

class Discovery(Debugger):
	DISCOVERY_TYPE_IDENTIFY = 'I'
	DISCOVERY_TYPE_NETWORK_CONFIG = 'N'

	def discover(self, cube_serial=None, discovery_type=DISCOVERY_TYPE_IDENTIFY):
		send_socket = None
		recv_socket = None

		try:
			send_socket = self._create_send_socket()
			payload = bytearray("eQ3Max", "utf-8") + \
						bytearray("*\0", "utf-8") + \
						bytearray(cube_serial or '*' * 10, 'utf-8') + \
						bytearray(discovery_type, 'utf-8')

			self.dump_bytes(payload, "Discovery packet")

			send_socket.sendto(payload, ("255.255.255.255", 23272))
			recv_socket = self._create_receive_socket()

			response = bytearray(recv_socket.recv(50))

			if discovery_type == Discovery.DISCOVERY_TYPE_IDENTIFY:
				return DiscoveryIdentifyResponse(response)
			elif discovery_type == Discovery.DISCOVERY_TYPE_NETWORK_CONFIG:
				return DiscoveryNetworkConfigurationResponse(response)
		finally:
			if send_socket:
				send_socket.close()
			if recv_socket:
				recv_socket.close()

	def _create_receive_socket(self):
		recv_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		recv_socket.settimeout(10)
		recv_socket.bind(("0.0.0.0", 23272))
		return recv_socket

	def _create_send_socket(self):
		send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
		send_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, True)
		send_socket.settimeout(10)
		return send_socket


class CubeConnectionException(Exception):
	pass


class Cube(object):

	def __init__(self, *args, **kwargs):
		addr = None
		port = 62910

		if not args:
			addr = kwargs.get('address', addr) or addr
			port = kwargs.get('port', port) or port
		if len(args) == 1:
			if isinstance(args[0], DiscoveryNetworkConfigurationResponse):
				addr = args[0].ip_address
			else:
				addr, = args
		elif len(args) == 2:
			addr, port = args

		self.addr_port = addr, port
		self._socket = None
		self._devices = DeviceList()
		self._cube_info = None
		self._ntp_servers = None
		self.received_messages = {}

	@property
	def socket(self):
		if self._socket is None:
			raise CubeConnectionException("Not connected")
		return self._socket

	def __enter__(self):
		self.connect()
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.disconnect()

	def connect(self):
		if self._socket:
			raise CubeConnectionException("Already connected")

		logger.info("Connecting to cube %s:%s", *self.addr_port)
		self._socket = self._create_socket()
		self.read()

	def _create_socket(self):
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.settimeout(1)
		s.connect(self.addr_port)
		return s

	def disconnect(self):
		if self._socket:
			self.send_message(QuitMessage())
			self._socket.close()
		self._socket = None

	def read(self):
		buffer_size = 4096
		buffer = bytearray([])
		more = True

		while more:
			try:
				logger.debug("socket.recv(%s)", buffer_size)
				tmp = self.socket.recv(buffer_size)
				logger.debug("Read %s bytes", len(tmp))
				more = len(tmp) > 0
				buffer += tmp
			except socket.timeout:
				break

		messages = buffer.splitlines()
		logger.debug("Processing %s messages", len(messages))

		while len(messages):
			current = messages[0]
			message_type = chr(current[0])

			if message_type in MultiPartResponses:
				multi_responses = [
					current[2:]
				]

				while len(messages) > 1 and chr(messages[1][0]) == message_type:
					multi_responses.append(messages.pop(1)[2:])

				logger.debug("'%s' message with %s parts", message_type, len(multi_responses))
				response = self.parse_message(message_type, multi_responses)
			else:
				logger.debug("'%s' single-part message", message_type)
				response = self.parse_message(message_type, current[2:])

			self.handle_message(response)

			messages.pop(0)
			logger.debug("Remaining: %s messages" % len(messages))

	def parse_message(self, message_type, buffer):
		message_classes = {
			HELLO_RESPONSE: HelloResponse,
			M_RESPONSE: MResponse,
			CONFIGURATION_RESPONSE: ConfigurationResponse,
			L_RESPONSE: LResponse,
			F_RESPONSE: FResponse,
			SET_RESPONSE: SetResponse,
		}

		clazz = message_classes.get(message_type, None)

		if clazz:
			response = clazz(buffer)
			logger.info("Received message %s: %s", type(response).__name__, response)
			self.received_messages[message_type] = response
			return response
		else:
			logger.warning("Cannot process message type %s", message_type)
			return None

	def handle_message(self, msg):
		logger.info("Handle message: %s", msg)
		if isinstance(msg, HelloResponse):
			self._cube_info = msg
		elif isinstance(msg, FResponse):
			self._ntp_servers = msg.ntp_servers
		elif isinstance(msg, MResponse):
			for idx, device_type, rf_address, serial, name, room_id in msg.devices:
				self.devices.update(rf_address=rf_address, serial=serial, name=name, room_id=room_id, device_type=device_type)
		elif isinstance(msg, ConfigurationResponse):
			self.devices.update(rf_address=msg.device_addr, configuration=msg)
		elif isinstance(msg, LResponse):
			self.devices.update(rf_address=msg.rf_addr, settings=msg)

	def send_message(self, msg):
		message_bytes = msg.to_bytes()
		logger.info("Sending '%s' message (%s bytes)", msg.__class__.__name__, len(message_bytes))
		self.socket.send(message_bytes)
		self.read()

	def get_message(self, message_type):
		return self.received_messages.get(message_type, None)

	@property
	def info(self):
		return self._cube_info

	@property
	def rooms(self):
		msg = self.get_message(M_RESPONSE)
		if msg:
			return [
				Room(*room_data, devices=[
					Device(rf_address=device_data[2], serial=device_data[3], name=device_data[4]) for device_data in filter(lambda x: x[5] == room_data[0], msg.devices)
				]) for room_data in msg.rooms
			]
		return []

	@property
	def devices(self):
		return self._devices

	def get_ntp_servers(self):
		if self._ntp_servers is None:
			self.send_message(FMessage())
		return self._ntp_servers

	def set_ntp_servers(self, ntp_servers):
		self.send_message(FMessage(ntp_servers))

	ntp_servers = property(get_ntp_servers, set_ntp_servers)

	def set_mode_auto(self, room, rf_addr):
		return self.set_mode(room, rf_addr, SetTemperatureAndModeMessage.ModeAuto)

	def set_mode_boost(self, room, rf_addr):
		return self.set_mode(room, rf_addr, SetTemperatureAndModeMessage.ModeBoost)

	def set_mode_manual(self, room, rf_addr, temperature):
		return self.set_mode(room, rf_addr, SetTemperatureAndModeMessage.ModeManual, temperature=temperature)

	def set_mode_vacation(self, room, rf_addr, temperature, end):
		return self.set_mode(room, rf_addr, SetTemperatureAndModeMessage.ModeVacation, temperature=temperature, end=end)

	def set_mode(self, room, rf_addr, mode, *args, **kwargs):
		self.send_message(SetTemperatureAndModeMessage(rf_addr, room, mode, **kwargs))
		return self.get_message(SET_RESPONSE)

	def set_program(self, room, rf_addr, weekday, program):
		self.send_message(SetProgramMessage(rf_addr, room, weekday, program))
		return self.get_message(SET_RESPONSE)

	def set_temperatures(self, room, rf_addr, comfort, eco, min, max, temperature_offset, window_open, window_open_duration):
		self.send_message(SetTemperaturesMessage(rf_addr, room, comfort, eco, min, max, temperature_offset, window_open, window_open_duration))
		return self.get_message(SET_RESPONSE)

	def set_valve_config(self, room, rf_addr, boost_duration, boost_valve_position, decalc_day, decalc_hour, max_valve_setting):
		self.send_message(SetValveConfigMessage(rf_addr, room, boost_duration, boost_valve_position, decalc_day, decalc_hour, max_valve_setting))
		return self.get_message(SET_RESPONSE)