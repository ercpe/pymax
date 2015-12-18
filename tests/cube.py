# -*- coding: utf-8 -*-
import logging
import socket
import unittest
import sys
import datetime

if sys.version_info.major == 2 or (sys.version_info.major == 3 and sys.version_info.minor <= 2):
	from mock import Mock
else:
	from unittest.mock import Mock

from pymax.messages import SetTemperatureAndModeMessage, FMessage, SetProgramMessage
from pymax.cube import Connection, Cube, Room, Device
from pymax.response import HELLO_RESPONSE, HelloResponse, M_RESPONSE, MResponse, SetResponse, CONFIGURATION_RESPONSE, \
	ConfigurationResponse, L_RESPONSE, LResponse, F_RESPONSE, FResponse, SET_RESPONSE
from response import HelloResponseBytes, MResponseBytes, CubeConfigurationBytes


class StaticResponseSocket(object):
	def __init__(self, responses):
		self.response = bytearray()
		for x in responses:
			self.response += x
			self.response += bytearray([0x0d, 0x0a])
		self.pos = 0

	def recv(self, size):
		if self.pos >= len(self.response):
			raise socket.timeout
		x = self.response[self.pos:self.pos + size]
		self.pos += size
		return x


class ConnectionTest(unittest.TestCase):

	def test_parse_message(self):

		for message_type, message_bytes, message_class in [
			(HELLO_RESPONSE, HelloResponseBytes, HelloResponse),
			(M_RESPONSE, MResponseBytes, MResponse),
			(CONFIGURATION_RESPONSE, CubeConfigurationBytes, ConfigurationResponse),
			(L_RESPONSE, bytearray(b"CxIrZfcSGWQ8AOsA"), LResponse),
			(F_RESPONSE, bytearray(b"ntp.homematic.com,ntp.homematic.com"), FResponse),
			(SET_RESPONSE, bytearray(b"00,0,31"), SetResponse),
		]:
			conn = Connection((None, None))

			conn.parse_message(message_type, message_bytes)

			self.assertEqual(len(conn.received_messages), 1)
			self.assertTrue(message_type in conn.received_messages.keys(), "Message of type %s not found in .received_messages" % message_type)
			self.assertIsInstance(conn.received_messages[message_type], message_class)

	def test_disconnect_not_connected(self):
		c = Mock(Connection)
		c.disconnect()
		self.assertFalse(c.send_message.called)

	def test_disconnect(self):
		fake_socket = Mock(socket.socket)
		fake_socket.recv = Mock(return_value=bytearray())
		fake_socket.close = Mock(return_value=None)

		c = Connection(('127.0.0.1', 62910))
		c.socket = fake_socket
		c.disconnect()
		self.assertTrue(fake_socket.close.called)
		self.assertIsNone(c.socket)

	def test_not_connected_read(self):
		c = Connection(('127.0.0.1', 62910))
		self.assertIsNone(c.read())

	def test_read(self):
		c = Connection(('127.0.0.1', 62910))
		c.socket = StaticResponseSocket([
			bytearray('H:', encoding='utf-8') + HelloResponseBytes,
			bytearray('M:', encoding='utf-8') + MResponseBytes
		])
		c.read()
		self.assertEqual(len(c.received_messages), 2)

	def test_read_unknown_response(self):
		c = Connection(('127.0.0.1', 62910))
		c.socket = StaticResponseSocket([
			bytearray('X:', encoding='utf-8'),
		])
		c.read()
		self.assertEqual(len(c.received_messages), 0)

	def test_get_message(self):
		c = Connection(('127.0.0.1', 62910))
		self.assertFalse(c.get_message(F_RESPONSE))

		c = Connection(('127.0.0.1', 62910))
		c.parse_message(F_RESPONSE, b"ntp.homematic.com,ntp.homematic.com")
		msg = FResponse(b"ntp.homematic.com,ntp.homematic.com")
		self.assertEqual(c.get_message(F_RESPONSE), msg)


class CubeTest(unittest.TestCase):

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

	def test_connect(self):
		c = Cube(connection=Mock())
		c.connect()
		self.assertTrue(c.connection.connect.called)

	def test_disconnect(self):
		c = Cube(connection=Mock())
		c.disconnect()
		self.assertFalse(c.connection.connect.called)
		self.assertTrue(c.connection.disconnect.called)

	def test_context_manager_connect_and_disconnect(self):
		with Cube(connection=Mock()) as cube:
			self.assertTrue(cube.connection.connect.called)

		self.assertTrue(cube.connection.disconnect.called)

	def test_context_manager_disconnect_on_exception(self):
		try:
			with Cube(connection=Mock()) as cube:
				raise Exception("just a test")
		except Exception as ex:
			self.assertTrue(cube.connection.connect.called)
			self.assertTrue(cube.connection.disconnect.called)
			self.assertEqual(ex.args, ("just a test", ))

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

	def test_get_ntp_servers(self):
		conn = Mock()
		conn.get_message = Mock(return_value=FResponse(bytearray("ntp.homematic.com,ntp.homematic.com", encoding='utf-8')))
		c = Cube(connection=conn)
		x = c.ntp_servers
		c.connection.send_message.assert_called_with(FMessage())

	def test_get_ntp_servers_no_response(self):
		conn = Mock()
		conn.get_message = Mock(return_value=None)
		c = Cube(connection=conn)
		c.ntp_servers
		c.connection.send_message.assert_called_with(FMessage())
		self.assertIsNone(c.ntp_servers)

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

	def test_set_program(self):
		c = self._mocked_cube()
		response = c.set_program(1, '122b56', 1, [])
		c.connection.send_message.assert_called_with(SetProgramMessage('122b56', 1, 1, []))
		self.assertIsInstance(response, SetResponse)