# -*- coding: utf-8 -*-
import unittest

from pymax.response import DiscoveryIdentifyResponse, BaseResponse, DiscoveryNetworkConfigurationResponse


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

	def test_parsing(self):
		b = bytearray([
			0x65, 0x51, 0x33, 0x4D, 0x61, 0x78, 0x41, 0x70, 0x4B, 0x45, 0x51, 0x30, 0x35, 0x32, 0x33, 0x38, 0x36, 0x34, 0x3E, 0x49, 0x00, 0x09, 0x7F, 0x2C, 0x01, 0x13])

		response = DiscoveryIdentifyResponse(b)

		self.assertEqual(response.name, 'eQ3MaxAp')
		self.assertEqual(response.serial, 'KEQ0523864')
		self.assertEqual(response.request_id, '>')
		self.assertEqual(response.request_type, 'I')
		self.assertEqual(response.rf_address, '097f2c')
		self.assertEqual(response.fw_version, '0113')



class DiscoveryNetworkConfigResponseTest(unittest.TestCase):

	def test_parsing(self):
		b = bytearray([
			0x65, 0x51, 0x33, 0x4d, 0x61, 0x78, 0x41, 0x70, 0x4B, 0x45, 0x51, 0x30, 0x35, 0x32, 0x33, 0x38, 0x36, 0x34, 0x3e, 0x4e, 0x0a, 0x0a, 0x0a, 0x99, 0x0a, 0x0a, 0x0a, 0x01, 0xff, 0xff, 0xff, 0x00, 0x0a, 0x0a, 0x0a, 0x01, 0x00, 0x00, 0x00, 0x00
		])

		response = DiscoveryNetworkConfigurationResponse(b)

		self.assertEqual(response.name, 'eQ3MaxAp')
		self.assertEqual(response.serial, 'KEQ0523864')
		self.assertEqual(response.request_id, '>')
		self.assertEqual(response.request_type, 'N')
		self.assertEqual(response.ip_address, '10.10.10.153')
		self.assertEqual(response.netmask, '255.255.255.0')
		self.assertEqual(response.gateway, '10.10.10.1')
		self.assertEqual(response.dns1, '10.10.10.1')
		self.assertEqual(response.dns2, '0.0.0.0')