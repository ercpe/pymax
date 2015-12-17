# -*- coding: utf-8 -*-
import base64
import unittest

import datetime

from pymax.messages import QuitMessage, FMessage, SetTemperatureAndModeMessage, SetProgramMessage
from pymax.objects import ProgramSchedule


class QuitMessageTest(unittest.TestCase):

	def test_bytes(self):
		m = QuitMessage()
		self.assertEqual(m.to_bytes(), bytearray(b'q:\r\n'))


class FMessageTest(unittest.TestCase):

	def test_bytes_query(self):
		msg = FMessage()
		self.assertEqual(msg.to_bytes(), bytearray(b'f:\r\n'))

	def test_bytes_set(self):
		msg = FMessage(['foo', 'bar'])
		self.assertEqual(msg.to_bytes(), bytearray(b'f:foo,bar\r\n'))


class SetTemperatureAndModeMessageTest(unittest.TestCase):

	def test_set_manual(self):
		msg = SetTemperatureAndModeMessage('122B65', 1, SetTemperatureAndModeMessage.ModeManual, temperature=19)

		b64payload = msg.to_bytes()[2:]
		data = base64.b64decode(b64payload)

		self.assertEqual(data, bytearray([
			0x00, 0x04, 0x40, 0x00, 0x00, 0x00, # base string
			0x12, 0x2b, 0x65, # rf addr
			0x01, # room
			0x66, # manual, temp = 19
		]))

	def test_set_auto(self):
		msg = SetTemperatureAndModeMessage('122B65', 1, SetTemperatureAndModeMessage.ModeAuto)

		b64payload = msg.to_bytes()[2:]
		data = base64.b64decode(b64payload)

		self.assertEqual(data, bytearray([
			0x00, 0x04, 0x40, 0x00, 0x00, 0x00, # base string
			0x12, 0x2b, 0x65, # rf addr
			0x01, # room
			0x0, # auto, temp = 0
		]))

	def test_set_boost(self):
		msg = SetTemperatureAndModeMessage('122B65', 1, SetTemperatureAndModeMessage.ModeBoost)

		b64payload = msg.to_bytes()[2:]
		data = base64.b64decode(b64payload)

		self.assertEqual(data, bytearray([
			0x00, 0x04, 0x40, 0x00, 0x00, 0x00, # base string
			0x12, 0x2b, 0x65, # rf addr
			0x01, # room
			0xc0, # boost, temp = 0
		]))

	def test_set_vacation(self):
		msg = SetTemperatureAndModeMessage('122B65', 1, SetTemperatureAndModeMessage.ModeVacation, temperature=29.5,
										   end=datetime.datetime(2015, 12, 15, 23, 00))

		b64payload = msg.to_bytes()[2:]
		data = base64.b64decode(b64payload)

		self.assertEqual(data, bytearray([
			0x00, 0x04, 0x40, 0x00, 0x00, 0x00, # base string
			0x12, 0x2b, 0x65, # rf addr
			0x01, # room
			0xBB, 0xCF, 0xF, 0x2E, # vacation, temp = 29.5, end = 15.12.2015, 23:00h
			#       | -  |     |
			#       date unt.
			#                  time until
			# | temp
		]))


class SetProgramMessageTest(unittest.TestCase):

	def test_constructor_no_schedule(self):
		msg = SetProgramMessage('foo', 1, 1, None)
		self.assertEqual(msg.program, [])

	def test_constructor_empty_schedule(self):
		msg = SetProgramMessage('foo', 1, 1, [])
		self.assertEqual(msg.program, [])

	def test_constructor_too_many_schedules(self):
		self.assertRaises(ValueError, SetProgramMessage, 'foo', 1, 1, [
			None, None, None, None, None, None, None, None, None, None, None, None, None, None,
		])

	def test_constructor_no_programschedules(self):
		self.assertRaises(ValueError, SetProgramMessage, 'foo', 1, 1, [
			1, 2, 3
		])

	def test_get_payload_empty(self):
		msg = SetProgramMessage('122b65', 1, 1, [
		])

		b64payload = msg.to_bytes()[2:]
		data = base64.b64decode(b64payload)

		self.assertEqual(data, bytearray([
			0x00, 0x04, 0x10, 0x00, 0x00, 0x00, # base string
			0x12, 0x2b, 0x65, # rf addr
			0x01, # room
			0x03, # weekday (*cube* weekday)
			# 0x00, 0x00,
			# 0x00, 0x00,
			# 0x00, 0x00,
			# 0x00, 0x00,
			# 0x00, 0x00,
			# 0x00, 0x00,
			# 0x00, 0x00,
		]))

	def test_get_payload_one(self):
		msg = SetProgramMessage('122b65', 1, 6, [
			ProgramSchedule(16, 0, datetime.time(6, 5))
		])

		b64payload = msg.to_bytes()[2:]
		data = base64.b64decode(b64payload)

		self.assertEqual(data, bytearray([
			0x00, 0x04, 0x10, 0x00, 0x00, 0x00, # base string
			0x12, 0x2b, 0x65, # rf addr
			0x01, # room
			0x01, # weekday (*cube* weekday)
			0x40, 0x49,
			# 0x00, 0x00,
			# 0x00, 0x00,
			# 0x00, 0x00,
			# 0x00, 0x00,
			# 0x00, 0x00,
			# 0x00, 0x00,
		]))