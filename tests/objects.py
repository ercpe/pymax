# -*- coding: utf-8 -*-
import unittest
import datetime

from pymax.objects import ProgramSchedule

class ProgramScheduleTest(unittest.TestCase):

	def test_constructor1(self):
		ps = ProgramSchedule(10, 60, 60)
		self.assertEqual(ps.temperature, 10)
		self.assertEqual(ps.begin_time, datetime.time(1))
		self.assertEqual(ps.end_time, datetime.time(1))

	def test_constructor2(self):
		ps = ProgramSchedule(10, datetime.time(1), 60)
		self.assertEqual(ps.temperature, 10)
		self.assertEqual(ps.begin_time, datetime.time(1))
		self.assertEqual(ps.end_time, datetime.time(1))

	def test_constructor3(self):
		ps = ProgramSchedule(10, 60, datetime.time(2))
		self.assertEqual(ps.temperature, 10)
		self.assertEqual(ps.begin_time, datetime.time(1))
		self.assertEqual(ps.end_time, datetime.time(2))

	def test_constructor4(self):
		ps = ProgramSchedule(10, datetime.time(1), datetime.time(1))
		self.assertEqual(ps.temperature, 10)
		self.assertEqual(ps.begin_time, datetime.time(1))
		self.assertEqual(ps.end_time, datetime.time(1))

