# -*- coding: utf-8 -*-
import base64
import unittest

import datetime

from pymax.messages import QuitMessage, FMessage, SetTemperatureAndModeMessage, SetProgramMessage, \
	SetTemperaturesMessage, SetValveConfigMessage
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
		msg = SetProgramMessage('122b65', 1, 1, [])

		b64payload = msg.to_bytes()[2:]
		data = base64.b64decode(b64payload)

		expected = bytearray([
			0x00, 0x04, 0x10, 0x00, 0x00, 0x00, # base string
			0x12, 0x2b, 0x65, # rf addr
			0x01, # room
			0x03, # weekday (*cube* weekday)
		])
		self.assertEqual(data, expected)

	def test_get_payload_one(self):
		msg = SetProgramMessage('122b65', 1, 6, [
			ProgramSchedule(16, 0, datetime.time(6, 5))
		])

		b64payload = msg.to_bytes()[2:]
		data = base64.b64decode(b64payload)

		expected = bytearray([
			0x00, 0x04, 0x10, 0x00, 0x00, 0x00, # base string
			0x12, 0x2b, 0x65, # rf addr
			0x01, # room
			0x01, # weekday (*cube* weekday)
			0x40, 0x49,
		])
		self.assertEqual(data, expected)

	def test_stupid_payload(self):
		expected = bytearray([int(x, 16) for x in "00 04 10 00 00 00 12 2b 65 01 02 40 49 4c 6e 40 cb 4d 20".split()])
		#                                             base string | rf addr |r| d  |s1   |s2   |s3   |s4
		msg = SetProgramMessage('122b65', 1, 0, [
			ProgramSchedule(16, datetime.time(), datetime.time(6, 5)),
			ProgramSchedule(19, datetime.time(6, 5), datetime.time(9, 10)),
			ProgramSchedule(16, datetime.time(9, 10), datetime.time(16, 55)),
			ProgramSchedule(19, datetime.time(16, 55), 1440),
		])
		data = msg.get_payload()

		# print("")
		# print(" ".join(["{0}".format(str(i).rjust(2, ' ')) for i in range(0, max(len(data), len(expected)))]))
		# print(" ".join(["{0:2X}".format(i) for i in bytearray(data)]))
		# print(" ".join(["{0:2X}".format(i) for i in expected]))
		# print("")

		self.assertEqual(data, expected)

class SetTemperaturesMessageTest(unittest.TestCase):

	def test_get_payload(self):
		msg = SetTemperaturesMessage('122b65', 1, 1, 2, 3, 4, 5, 6, 10)
		b64payload = msg.to_bytes()[2:]
		data = base64.b64decode(b64payload)

		self.assertEqual(data, bytearray([
			0x00, 0x00, 0x11, 0x00, 0x00, 0x00, # base string
			0x12, 0x2b, 0x65, # rf addr
			0x01, # room
			0x02, # comfort
			0x04, # eco
			0x08, # max
			0x06, # min
			0x11, # offset
			0x0c, # window open temp
			0x02, # window open duration
		]))


class SetValveSettingsMessageTest(unittest.TestCase):

	def test_constructor(self):
		# boost valve position is an integer (e.g. 80 for 80%)
		msg = SetValveConfigMessage('122b65', 1, 10, 80, 1, 2, 100)
		self.assertEqual(msg.boost_valve_position, 0.8)

		# boost valve position is a float (e.g. 0.8 for 80%)
		msg = SetValveConfigMessage('122b65', 1, 10, 0.8, 1, 2, 100)
		self.assertEqual(msg.boost_valve_position, 0.8)

	def test_get_payload(self):
		msg = SetValveConfigMessage('122b65', 1, 10, 80, 1, 2, 100)

		b64payload = msg.to_bytes()[2:]
		data = base64.b64decode(b64payload)

		self.assertEqual(data, bytearray([
			0x00, 0x04, 0x12, 0x00, 0x00, 0x00, # base string
			0x12, 0x2b, 0x65, # rf addr
			0x01, # room
			0x50, # boost
			0x62, # decalc
			0xFF, # max valve setting
			0x00, # valve offset
		]))