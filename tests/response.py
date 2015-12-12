# -*- coding: utf-8 -*-
import unittest

from pymax.response import DiscoveryIdentifyResponse


class DiscoveryIdentifyResponseTest(unittest.TestCase):

	def test_parsing_errors(self):
		self.assertRaises(ValueError, DiscoveryIdentifyResponse, (None,)) # empty
		self.assertRaises(ValueError, DiscoveryIdentifyResponse, (bytearray(),)) # empty
		self.assertRaises(ValueError, DiscoveryIdentifyResponse, (bytearray([0 for _ in range(0, 10)]),))  # too short
		self.assertRaises(ValueError, DiscoveryIdentifyResponse, (bytearray([0 for _ in range(0, 100)]),))  # too long

	def test_parsing(self):

		b = bytearray([0x65, 0x51, 0x33, 0x4D, 0x61, 0x78, 0x41, 0x70, 0x4B, 0x45, 0x51, 0x30, 0x35, 0x32, 0x33, 0x38, 0x36, 0x34, 0x3E, 0x49, 0x00, 0x09, 0x7F, 0x2C, 0x01, 0x13])

		response = DiscoveryIdentifyResponse(b)

		self.assertEqual(response.name, 'eQ3MaxAp')
		self.assertEqual(response.serial, 'KEQ0523864')
		self.assertEqual(response.request_id, '>')
		self.assertEqual(response.request_type, 'I')
		self.assertEqual(response.rf_address, '097f2c')
		self.assertEqual(response.fw_version, '0113')
