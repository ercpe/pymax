# -*- coding: utf-8 -*-
import socket

import logging

import collections

from pymax.messages import QuitMessage, FMessage, SetTemperatureAndModeMessage
from pymax.response import DiscoveryIdentifyResponse, DiscoveryNetworkConfigurationResponse, HelloResponse, MResponse, \
	HELLO_RESPONSE, M_RESPONSE, MultiPartResponses, CONFIGURATION_RESPONSE, ConfigurationResponse, L_RESPONSE, LResponse, \
	F_RESPONSE, FResponse, SET_RESPONSE, SetResponse
from pymax.util import Debugger

logger = logging.getLogger(__name__)

Room = collections.namedtuple('Room', ('room_id', 'name', 'rf_address', 'devices'))
Device = collections.namedtuple('Device', ('type', 'rf_address', 'serial', 'name'))

class Discovery(Debugger):
	DISCOVERY_TYPE_IDENTIFY = 'I'
	DISCOVERY_TYPE_NETWORK_CONFIG = 'N'

	def discover(self, cube_serial=None, discovery_type=DISCOVERY_TYPE_IDENTIFY):
		send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
		send_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, True)
		send_socket.settimeout(10)

		payload = bytearray("eQ3Max", "utf-8") + \
					bytearray("*\0", "utf-8") + \
					bytearray(cube_serial or '*' * 10, 'utf-8') + \
					bytearray(discovery_type, 'utf-8')

		self.dump_bytes(payload, "Discovery packet")

		send_socket.sendto(payload, ("10.10.10.255", 23272))

		recv_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		recv_socket.settimeout(10)
		recv_socket.bind(("0.0.0.0", 23272))

		response = bytearray(recv_socket.recv(50))

		if discovery_type == Discovery.DISCOVERY_TYPE_IDENTIFY:
			return DiscoveryIdentifyResponse(response)
		elif discovery_type == Discovery.DISCOVERY_TYPE_NETWORK_CONFIG:
			return DiscoveryNetworkConfigurationResponse(response)

		send_socket.close()
		recv_socket.close()


class Connection(Debugger):
	MESSAGE_Q = 'q'  # quit

	def __init__(self, conn):
		self.addr_port = conn
		self.socket = None
		self.received_messages = {}

	def connect(self):
		if self.socket:
			logger.error(".connect() called when socket already present")
		else:
			logger.info("Connecting to cube %s:%s" % self.addr_port)
			self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.socket.settimeout(1)
			self.socket.connect(self.addr_port)
			self.read()

	def read(self):
		if not self.socket:
			logger.error(".read() called when not connected")
			return

		buffer_size = 4096
		buffer = bytearray([])
		more = True

		while more:
			try:
				logger.debug("socket.recv(%s)" % buffer_size)
				tmp = self.socket.recv(buffer_size)
				logger.debug("Read %s bytes" % len(tmp))
				more = len(tmp) > 0
				buffer += tmp
			except socket.timeout:
				break

		messages = buffer.splitlines()
		logger.debug("Processing %s messages" % len(messages))

		while len(messages):
			current = messages[0]
			message_type = chr(current[0])

			if message_type in MultiPartResponses:
				multi_responses = [
					current[2:]
				]

				while len(messages) > 1 and chr(messages[1][0]) == message_type:
					multi_responses.append(messages.pop(1)[2:])

				logger.info("'%s' message with %s parts" % (message_type, len(multi_responses)))
				self.parse_message(message_type, multi_responses)
			else:
				logger.info("'%s' single-part message" % message_type)
				self.parse_message(message_type, current[2:])

			messages.pop(0)
			logger.debug("Remaining: %s messages" % len(messages))

	def parse_message(self, message_type, buffer):
		response = None
		if message_type == HELLO_RESPONSE:
			response = HelloResponse(buffer)
		elif message_type == M_RESPONSE:
			response = MResponse(buffer)
		elif message_type == CONFIGURATION_RESPONSE:
			response = ConfigurationResponse(buffer)
		elif message_type == L_RESPONSE:
			response = LResponse(buffer)
		elif message_type == F_RESPONSE:
			response = FResponse(buffer)
		elif message_type == SET_RESPONSE:
			response = SetResponse(buffer)
		else:
			logger.warning("Cannot process message type %s" % message_type)

		if response:
			logger.info("Received message %s: %s" % (type(response).__name__, response))
			self.received_messages[message_type] = response

	def send_message(self, msg):
		message_bytes = msg.to_bytes()
		logger.info("Sending '%s' message (%s bytes)" % (msg.__class__.__name__, len(message_bytes)))
		if not self.socket:
			self.connect()
		self.socket.send(message_bytes)
		self.read()

	def get_message(self, message_type):
		return self.received_messages.get(message_type, None)

	def disconnect(self):
		if self.socket:
			self.send_message(QuitMessage())
			self.socket.close()
		self.socket = None


class Cube(object):

	def __init__(self, *args, **kwargs):
		addr = None
		port = 62910

		if len(args) == 1:
			addr, = args
		elif len(args) == 2:
			addr, port = args

		conn = kwargs.get('connection', None)
		if not conn:
			addr = kwargs.get('address', addr)
			port = kwargs.get('port', port)
			conn = Connection((addr, port))
		self.connection = conn

	def __enter__(self):
		self.connection.connect()
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.connection.disconnect()

	def connect(self):
		self.connection.connect()

	def disconnect(self):
		self.connection.disconnect()

	@property
	def rooms(self):
		msg = self.connection.get_message(M_RESPONSE)
		if msg:
			return [
				Room(*room_data, devices=[
					Device(device_data[1], device_data[2], device_data[3], device_data[4]) for device_data in filter(lambda x: x[5] == room_data[0], msg.devices)
				]) for room_data in msg.rooms
			]
		return []

	def get_ntp_servers(self):
		self.connection.send_message(FMessage())
		fmsg = self.connection.get_message(F_RESPONSE)
		if fmsg:
			return fmsg.ntp_servers
		return None

	def set_ntp_servers(self, ntp_servers):
		self.connection.send_message(FMessage(ntp_servers))

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
		self.connection.send_message(SetTemperatureAndModeMessage(rf_addr, room, mode, **kwargs))
		return self.connection.get_message(SET_RESPONSE)
