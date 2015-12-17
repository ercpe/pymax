# -*- coding: utf-8 -*-
import unittest

import datetime

from pymax.util import dateuntil_to_date, date_to_dateuntil, unpack_temp_and_time, pack_temp_and_time, \
	cube_day_to_py_day, py_day_to_cube_day


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

	def test_pack_temp_and_time(self):
		arr = pack_temp_and_time(16, datetime.time(6, 5))

		self.assertEqual(arr, bytearray([0x40, 0x49]))

	def test_cube_day_to_py_day(self):
		for cube_day, py_day in (
			(0, 5),
			(1, 6),
			(2, 0),
			(3, 1),
			(4, 2),
			(5, 3),
			(6, 4)
		):
			self.assertEqual(cube_day_to_py_day(cube_day), py_day)

	def test_py_day_to_cube_day(self):
		for py_day, cube_day in (
			(0, 2),
			(1, 3),
			(2, 4),
			(3, 5),
			(4, 6),
			(5, 0),
			(6, 1),
		):
			self.assertEqual(py_day_to_cube_day(py_day), cube_day)