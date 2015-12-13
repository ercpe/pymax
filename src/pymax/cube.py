# -*- coding: utf-8 -*-
import socket

import logging

import collections

from pymax.messages import QuitMessage
from pymax.response import DiscoveryIdentifyResponse, DiscoveryNetworkConfigurationResponse, HelloResponse, MResponse, \
	HELLO_RESPONSE, M_RESPONSE, MultiPartResponses
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

	def disconnect(self):
		if self.socket:
			self.send_message(QuitMessage())
			self.socket.close()
		self.socket = None


class Cube(object):

	def __init__(self, address, port=62910):
		self.connection = Connection((address, port))

	def __enter__(self):
		self.connection.connect()
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.connection.disconnect()

	@property
	def rooms(self):
		if M_RESPONSE in self.connection.received_messages:
			mr = self.connection.received_messages[M_RESPONSE]
			return [
				Room(*room_data, devices=[
					Device(device_data[1], device_data[2], device_data[3], device_data[4]) for device_data in filter(lambda x: x[5] == room_data[0], mr.devices)
				]) for room_data in mr.rooms
			]
		return []
