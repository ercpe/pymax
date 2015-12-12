# -*- coding: utf-8 -*-
from pymax.util import Debugger


class BaseResponse(Debugger):
	length = None
	min_length = None
	max_length = None

	def __init__(self, response):
		if self.length is not None and len(response) != self.length:
			raise ValueError("Byte array must be %s bytes in length (is %s)" % (self.length, len(response)))

		if self.min_length is not None and len(response) < self.min_length:
			raise ValueError("Byte array must be at least %s bytes in length (is %s)" % (self.length, len(response)))

		if self.max_length is not None and len(response) > self.max_length:
			raise ValueError("Byte array must be at most %s bytes in length (is %s)" % (self.length, len(response)))

		self.response = response
		self.dump_bytes(response)
		self._parse()

	def _parse(self):
		raise NotImplemented


class DiscoveryIdentifyResponse(BaseResponse):
	length = 26

	def _parse(self):
		self.name = str(self.response[0:8])
		self.serial = str(self.response[8:18])
		self.request_id = unichr(self.response[18])
		self.request_type = unichr(self.response[19])
		self.rf_address = ''.join("%02x" % x for x in self.response[20:23])
		self.fw_version = ''.join("%02x" % x for x in self.response[24:26])

	def __str__(self):
		return "%s: RF addr: %s, FW version: %s" % (self.serial, self.rf_address, self.fw_version)

class DiscoveryNetworkConfigurationResponse(BaseResponse):
	length = 40

	def _parse(self):
		self.name = str(self.response[0:8])
		self.serial = str(self.response[8:18])
		self.request_id = unichr(self.response[18])
		self.request_type = unichr(self.response[19])
		self.ip_address = '.'.join([str(x) for x in self.response[20:24]])
		self.gateway = '.'.join([str(x) for x in self.response[24:28]])
		self.netmask = '.'.join([str(x) for x in self.response[28:32]])
		self.dns1 = '.'.join([str(x) for x in self.response[32:36]])
		self.dns2 = '.'.join([str(x) for x in self.response[36:40]])

	def __str__(self):
		return "%s: IP: %s, Netmask: %s, Gateway: %s, DNS1: %s, DNS2: %s" % (self.serial, self.ip_address, self.netmask, self.gateway, self.dns1, self.dns2)