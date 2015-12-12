# -*- coding: utf-8 -*-
import unittest

from pymax.response import DiscoveryIdentifyResponse


class DiscoveryIdentifyResponseTest(unittest.TestCase):

	def test_parsing_errors(self):
		self.assertRaises(ValueError, DiscoveryIdentifyResponse, (None,)) # empty
		self.assertRaises(ValueError, DiscoveryIdentifyResponse, (bytearray(),)) # empty
		self.assertRaises(ValueError, DiscoveryIdentifyResponse, (bytearray([0 for _ in range(0, 10)]),))  # too short
		self.assertRaises(ValueError, DiscoveryIdentifyResponse, (bytearray([0 for _ in range(0, 100)]),))  # too long
