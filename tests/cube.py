# -*- coding: utf-8 -*-
import unittest
import sys

import datetime

from pymax.messages import SetTemperatureAndModeMessage, FMessage

if sys.version_info.major == 2 or (sys.version_info.major == 3 and sys.version_info.minor <= 2):
	from mock import MagicMock, Mock
else:
	from unittest.mock import MagicMock, Mock

from pymax.cube import Connection, Cube, Room, Device
from pymax.response import HELLO_RESPONSE, HelloResponse, M_RESPONSE, MResponse, SetResponse
from response import HelloResponseBytes, MResponseBytes

class ConnectionTest(unittest.TestCase):

	def test_constructor(self):
		c = Cube('1.2.3.4')
		self.assertEqual(c.connection.addr_port, ('1.2.3.4', 62910))

		c = Cube('1.2.3.4', 4567)
		self.assertEqual(c.connection.addr_port, ('1.2.3.4', 4567))

		c = Cube(address='1.2.3.4')
		self.assertEqual(c.connection.addr_port, ('1.2.3.4', 62910))

		c = Cube(address='1.2.3.4', port=9876)
		self.assertEqual(c.connection.addr_port, ('1.2.3.4', 9876))

		c = Cube(connection=Connection(('1.2.3.4', 123)))
		self.assertEqual(c.connection.addr_port, ('1.2.3.4', 123))

	def test_parse_message(self):

		for message_type, message_bytes, message_class in [
			(HELLO_RESPONSE, HelloResponseBytes, HelloResponse),
			(M_RESPONSE, MResponseBytes, MResponse),
		]:

			conn = Connection((None, None))

			conn.parse_message(message_type, message_bytes)

			self.assertEqual(len(conn.received_messages), 1)
			self.assertTrue(message_type in conn.received_messages.keys(), "Message of type %s not found in .received_messages" % message_type)
			self.assertIsInstance(conn.received_messages[message_type], message_class)

	def test_connect(self):
		c = Cube(connection=Mock())
		c.connect()
		self.assertTrue(c.connection.connect.called)

	def test_disconnect(self):
		c = Cube(connection=Mock())
		c.disconnect()
		self.assertFalse(c.connection.connect.called)
		self.assertTrue(c.connection.disconnect.called)

	def _mocked_cube(self):
		conn = Mock()
		conn.get_message = Mock(return_value=SetResponse(bytearray("00,0,31", encoding='utf-8')))
		return Cube(connection=conn)

	def test_set_mode_auto(self):
		c = self._mocked_cube()
		response = c.set_mode_auto(123, '001122')
		c.connection.send_message.assert_called_with(SetTemperatureAndModeMessage('001122', 123, 0x0))
		self.assertIsInstance(response, SetResponse)

	def test_set_mode_boost(self):
		c = self._mocked_cube()
		response = c.set_mode_boost(123, '001122')
		c.connection.send_message.assert_called_with(SetTemperatureAndModeMessage('001122', 123, 0xc0))
		self.assertIsInstance(response, SetResponse)

	def test_set_mode_manual(self):
		c = self._mocked_cube()
		response = c.set_mode_manual(123, '001122', temperature=123)
		c.connection.send_message.assert_called_with(SetTemperatureAndModeMessage('001122', 123, 0x40, temperature=123))
		self.assertIsInstance(response, SetResponse)

	def test_set_mode_vacation(self):
		c = self._mocked_cube()
		response = c.set_mode_vacation(123, '001122', temperature=123, end=datetime.datetime(2015, 12, 16, 12, 00, 00))
		c.connection.send_message.assert_called_with(SetTemperatureAndModeMessage('001122', 123, 0x80, temperature=123, end=datetime.datetime(2015, 12, 16, 12, 00, 00)))
		self.assertIsInstance(response, SetResponse)

	def test_set_ntp_servers(self):
		c = self._mocked_cube()
		x = c.ntp_servers
		c.connection.send_message.assert_called_with(FMessage())

	def test_set_ntp_servers(self):
		c = self._mocked_cube()
		c.ntp_servers = ['foo', 'bar']
		c.connection.send_message.assert_called_with(FMessage(['foo', 'bar']))

	def test_rooms_no_messages(self):
		connection = Mock()
		connection.get_message = Mock(return_value=None)
		c = Cube(connection=connection)
		self.assertEqual(c.rooms, [])

	def test_rooms(self):
		connection = Mock()
		connection.get_message = Mock(return_value=MResponse([MResponseBytes]))
		c = Cube(connection=connection)
		self.assertEqual(c.rooms, [
			Room(room_id=1, name='Wohnzimmer', rf_address='122B65', devices=[
				Device(type=2, rf_address='122B65', serial='MEQ1472997', name='Heizung'),
			])
		])
