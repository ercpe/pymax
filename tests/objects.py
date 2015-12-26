# -*- coding: utf-8 -*-
import unittest
import datetime

from pymax.objects import ProgramSchedule, DeviceList, RFAddr


class ProgramScheduleTest(unittest.TestCase):

	def test_constructor1(self):
		ps = ProgramSchedule(10, 60, 60)
		self.assertEqual(ps.temperature, 10)
		self.assertEqual(ps.begin_minutes, 60)
		self.assertEqual(ps.end_minutes, 60)

	def test_constructor2(self):
		ps = ProgramSchedule(10, datetime.time(1), 60)
		self.assertEqual(ps.temperature, 10)
		self.assertEqual(ps.begin_minutes, 60)
		self.assertEqual(ps.end_minutes, 60)

	def test_constructor3(self):
		ps = ProgramSchedule(10, 60, datetime.time(2))
		self.assertEqual(ps.temperature, 10)
		self.assertEqual(ps.begin_minutes, 60)
		self.assertEqual(ps.end_minutes, 120)

	def test_constructor4(self):
		ps = ProgramSchedule(10, datetime.time(1), datetime.time(1))
		self.assertEqual(ps.temperature, 10)
		self.assertEqual(ps.begin_minutes, 60)
		self.assertEqual(ps.end_minutes, 60)


class DeviceListTest(unittest.TestCase):

	def test_for_room(self):
		dl = DeviceList()
		self.assertEqual(list(dl.for_room(0)), [])


class RFAddrTest(unittest.TestCase):

	def test_constructor_invalid_values(self):
		self.assertRaises(ValueError, RFAddr, None)
		self.assertRaises(ValueError, RFAddr, '')
		self.assertRaises(ValueError, RFAddr, bytearray())

		self.assertRaises(ValueError, RFAddr, bytearray([0x01]))
		self.assertRaises(ValueError, RFAddr, 'a')

	def test_constructor_valid_values(self):
		self.assertEqual(RFAddr('122b65')._bytes, bytearray([0x12, 0x2b, 0x65]))
		self.assertEqual(RFAddr(bytearray([0x12, 0x2b, 0x65]))._bytes, bytearray([0x12, 0x2b, 0x65]))
		self.assertEqual(RFAddr((0x12, 0x2b, 0x65))._bytes, bytearray([0x12, 0x2b, 0x65]))


	def test_equals(self):
		# string: case insensitive
		self.assertEqual(RFAddr('122b65'), '122b65')
		self.assertEqual(RFAddr('122b65'), '122B65')

		# another rf addr instance
		self.assertEqual(RFAddr('122b65'), RFAddr('122b65'))

		# bytearray
		self.assertEqual(RFAddr('122b65'), bytearray([0x12, 0x2b, 0x65]))

	def test_repr(self):
		addr = RFAddr('122b65')
		self.assertEqual(str(addr), repr(addr))