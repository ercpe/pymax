# -*- coding: utf-8 -*-
import unittest

import datetime

from pymax.util import dateuntil_to_date, date_to_dateuntil, unpack_temp_and_time


class UtilsTest(unittest.TestCase):

	def test_dateuntil_to_date(self):
		dt = dateuntil_to_date(bytearray([0x9d, 0x4b]))
		self.assertEqual(dt, datetime.date(2011, 9, 29))

	def test_dateuntil_to_date2(self):
		dt = dateuntil_to_date(bytearray([0x9d, 0x0b]))
		self.assertEqual(dt, datetime.date(2011, 8, 29))

	def test_date_to_dateuntil(self):
		du = date_to_dateuntil(datetime.date(2011, 8, 29))
		self.assertEqual(du, bytearray([0x9d, 0x0b]))

	def test_date_to_dateuntil(self):
		du = date_to_dateuntil(datetime.date(2011, 9, 29))
		self.assertEqual(du, bytearray([0x9d, 0x4b]))

	def test_invalid_date_to_dateuntil(self):
		self.assertRaises(ValueError, date_to_dateuntil, datetime.date(1999, 1, 1))

	def test_unpack_temp_and_time(self):
		temperature, minutes = unpack_temp_and_time(bytearray([0x40, 0x49]))

		self.assertEqual(temperature, 16)
		self.assertEqual(minutes, 365)

	def test_unpack_temp_and_time2(self):
		temperature, minutes = unpack_temp_and_time(bytearray([0x41, 0x49]))

		self.assertEqual(temperature, 16)
		self.assertEqual(minutes, 329)
