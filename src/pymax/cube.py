# -*- coding: utf-8 -*-
import socket

import logging

from pymax.response import DiscoveryIdentifyResponse, DiscoveryNetworkConfigurationResponse, HelloResponse
from pymax.util import Debugger

logger = logging.getLogger(__name__)

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

		for message in buffer.splitlines():
			self.parse_message(message)

	def parse_message(self, buffer):
		message_type = buffer[0:1]

		response = None
		if message_type == b'H':
			response = HelloResponse(buffer)
		else:
			logger.warning("Cannot process message type %s" % message_type)

		logger.info("Received message %s: %s" % (type(response).__name__, response))

	def send_message(self, msg, payload=None):
		logger.info("Sending '%s' message with %s bytes of payload" % (msg, len(payload or [])))
		if not self.socket:
			self.connect()
		data = (msg + ':').encode('utf-8')
		if payload:
			data += bytearray(payload)
		data += bytearray(b"\r\n")
		self.socket.send(data)

	def disconnect(self):
		if self.socket:
			self.send_message(Connection.MESSAGE_Q)
			self.socket.close()
		self.socket = None


class Cube(object):

	def __init__(self, address, port=62910):
		self.connection = Connection((address, port))

	def __enter__(self):
		self.connection.connect()

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.connection.disconnect()
