# -*- coding: utf-8 -*-
import unittest
import datetime

from pymax.response import DiscoveryIdentifyResponse, BaseResponse, DiscoveryNetworkConfigurationResponse, HelloResponse

class BaseResponseTest(unittest.TestCase):

	def test_fix_length(self):
		class FixedLengthResponse(BaseResponse):
			length = 5

			def _parse(self):
				pass

		self.assertRaises(ValueError, FixedLengthResponse, None) # empty
		self.assertRaises(ValueError, FixedLengthResponse, bytearray()) # empty
		self.assertRaises(ValueError, FixedLengthResponse, bytearray([0]))  # too short
		self.assertRaises(ValueError, FixedLengthResponse, bytearray([0, 0]))  # too short
		self.assertRaises(ValueError, FixedLengthResponse, bytearray([0 for _ in range(0, 100)]))  # too long

	def test_min_length(self):
		class MinLengthResponse(BaseResponse):
			min_length = 5

			def _parse(self):
				pass

		self.assertRaises(ValueError, MinLengthResponse, None) # empty
		self.assertRaises(ValueError, MinLengthResponse, bytearray()) # empty
		self.assertRaises(ValueError, MinLengthResponse, bytearray([0]))  # too short

	def test_max_length(self):
		class MaxLengthResponse(BaseResponse):
			max_length = 5

			def _parse(self):
				pass

		self.assertRaises(ValueError, MaxLengthResponse, None) # empty
		self.assertRaises(ValueError, MaxLengthResponse, bytearray()) # empty
		self.assertRaises(ValueError, MaxLengthResponse, bytearray([0 for _ in range(0, 100)]))  # too long


class DiscoveryIdentifyResponseTest(unittest.TestCase):

	def _make_response(self):
		b = bytearray([
			0x65, 0x51, 0x33, 0x4D, 0x61, 0x78, 0x41, 0x70,
			0x4B, 0x45, 0x51, 0x30, 0x35, 0x32, 0x33, 0x38, 0x36, 0x34,
			0x3E,
			0x49,
			0x00, 0x09, 0x7F, 0x2C,
			0x01, 0x13])

		return DiscoveryIdentifyResponse(b)

	def test_parsing(self):
		response = self._make_response()
		self.assertEqual(response.name, 'eQ3MaxAp')
		self.assertEqual(response.serial, 'KEQ0523864')
		self.assertEqual(response.request_id, '>')
		self.assertEqual(response.request_type, 'I')
		self.assertEqual(response.rf_address, '097f2c')
		self.assertEqual(response.fw_version, '0113')

	def test_str(self):
		response = self._make_response()
		self.assertEqual(str(response), "KEQ0523864: RF addr: 097f2c, FW version: 0113")


class DiscoveryNetworkConfigResponseTest(unittest.TestCase):

	def _make_response(self):
		b = bytearray([
			0x65, 0x51, 0x33, 0x4d, 0x61, 0x78, 0x41, 0x70,
			0x4B, 0x45, 0x51, 0x30, 0x35, 0x32, 0x33, 0x38, 0x36, 0x34,
			0x3e,
			0x4e,
			0x0a, 0x0a, 0x0a, 0x99,
			0x0a, 0x0a, 0x0a, 0x01,
			0xff, 0xff, 0xff, 0x00,
			0x0a, 0x0a, 0x0a, 0x01,
			0x00, 0x00, 0x00, 0x00
		])

		return DiscoveryNetworkConfigurationResponse(b)

	def test_parsing(self):
		response = self._make_response()
		self.assertEqual(response.name, 'eQ3MaxAp')
		self.assertEqual(response.serial, 'KEQ0523864')
		self.assertEqual(response.request_id, '>')
		self.assertEqual(response.request_type, 'N')
		self.assertEqual(response.ip_address, '10.10.10.153')
		self.assertEqual(response.netmask, '255.255.255.0')
		self.assertEqual(response.gateway, '10.10.10.1')
		self.assertEqual(response.dns1, '10.10.10.1')
		self.assertEqual(response.dns2, '0.0.0.0')


class HelloResponseTest(unittest.TestCase):

	def _make_response(self):
		b = bytearray([
			0x48, 0x3A,
			0x4B, 0x45, 0x51, 0x30, 0x35, 0x32, 0x33, 0x38, 0x36, 0x34, 0x2C,
			0x31, 0x30, 0x62, 0x31, 0x39, 0x39, 0x2C,
			0x30, 0x31, 0x31, 0x33, 0x2C,
			0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x2C,
			0x35, 0x34, 0x32, 0x34, 0x33, 0x63, 0x64, 0x64, 0x2C,
			0x30, 0x30, 0x2C,
			0x33, 0x32, 0x2C,
			0x30, 0x66, 0x30, 0x63, 0x30, 0x64, 0x2C,
			0x30, 0x38, 0x31, 0x32, 0x2C,
			0x30, 0x33, 0x2C,
			0x30, 0x30, 0x30, 0x30
		])
		return HelloResponse(b)

	def test_parsing(self):
		response = self._make_response()
		self.assertEqual(response.serial, 'KEQ0523864')
		self.assertEqual(response.rf_address, '10b199')
		self.assertEqual(response.fw_version, '0113')
		self.assertEqual(response.datetime, datetime.datetime(2015, 12, 13, 8, 18, 0))

	def test_str(self):
		response = self._make_response()
		self.assertEqual(str(response), "KEQ0523864: RF addr: 10b199, FW: 0113, Date: 2015-12-13 08:18:00")