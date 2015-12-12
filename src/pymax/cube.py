# -*- coding: utf-8 -*-
import socket

import logging

from pymax.response import DiscoveryIdentifyResponse, DiscoveryNetworkConfigurationResponse
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

class Cube(object):
	pass
