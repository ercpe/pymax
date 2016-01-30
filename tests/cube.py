# -*- coding: utf-8 -*-
import socket
import unittest
import sys
import datetime

from pymax.objects import DeviceList

if sys.version_info.major == 2 or (sys.version_info.major == 3 and sys.version_info.minor <= 2):
	from mock import Mock
else:
	from unittest.mock import Mock

from pymax.messages import SetTemperatureAndModeMessage, FMessage, SetProgramMessage, SetTemperaturesMessage, \
	SetValveConfigMessage
from pymax.cube import Cube, Room, Device, CubeConnectionException, Discovery
from pymax.response import HELLO_RESPONSE, HelloResponse, M_RESPONSE, MResponse, SetResponse, CONFIGURATION_RESPONSE, \
	ConfigurationResponse, L_RESPONSE, LResponse, F_RESPONSE, FResponse, SET_RESPONSE, \
	DiscoveryNetworkConfigurationResponse, DiscoveryIdentifyResponse
from response import HelloResponseBytes, MResponseBytes, CubeConfigurationBytes, DiscoveryNetworkConfigResponseBytes, \
	DiscoveryIdentifyResponseBytes, DiscoveryIdentifyRequestBytes, DiscoveryNetworkConfigRequestBytes, \
	ThermostatConfigurationBytes


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


class DiscoveryTest(unittest.TestCase):

	def _create_fake_send_socket(self):
		s = Mock(socket.socket)
		s.close = Mock()
		return s

	def _create_fake_receive_socket(self, recv_bytes):
		s = Mock(socket.socket)
		s.recv = Mock(return_value=recv_bytes)
		s.close = Mock()
		return s

	def test_identify_discover(self):
		send_socket = self._create_fake_send_socket()
		recv_socket = self._create_fake_receive_socket(DiscoveryIdentifyResponseBytes)

		d = Discovery()
		d._create_send_socket = Mock(return_value=send_socket)
		d._create_receive_socket = Mock(return_value=recv_socket)

		response = d.discover()
		send_socket.sendto.assert_called_with(DiscoveryIdentifyRequestBytes, ("255.255.255.255", 23272))
		self.assertEqual(response, DiscoveryIdentifyResponse(DiscoveryIdentifyResponseBytes))

		self.assertTrue(send_socket.close.called)
		self.assertTrue(recv_socket.close.called)

	def test_network_config_discover(self):
		send_socket = self._create_fake_send_socket()
		recv_socket = self._create_fake_receive_socket(DiscoveryNetworkConfigResponseBytes)

		d = Discovery()
		d._create_send_socket = Mock(return_value=send_socket)
		d._create_receive_socket = Mock(return_value=recv_socket)

		response = d.discover("KEQ0523864", Discovery.DISCOVERY_TYPE_NETWORK_CONFIG)
		send_socket.sendto.assert_called_with(DiscoveryNetworkConfigRequestBytes, ("255.255.255.255", 23272))
		self.assertEqual(response, DiscoveryNetworkConfigurationResponse(DiscoveryNetworkConfigResponseBytes))

		self.assertTrue(send_socket.close.called)
		self.assertTrue(recv_socket.close.called)


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
			#conn = Connection((None, None), message_handler=lambda x: x)
			conn = Cube((None, None))

			conn.parse_message(message_type, message_bytes)

			self.assertEqual(len(conn.received_messages), 1)
			self.assertTrue(message_type in conn.received_messages.keys(), "Message of type %s not found in .received_messages" % message_type)
			self.assertIsInstance(conn.received_messages[message_type], message_class)

	def test_disconnect_not_connected(self):
		c = Cube('127.0.0.1', 62910)
		c.disconnect()

	def test_disconnect(self):
		fake_socket = Mock(socket.socket)
		fake_socket.recv = Mock(return_value=bytearray())
		fake_socket.close = Mock(return_value=None)

		c = Cube('127.0.0.1', 62910)
		c._socket = fake_socket
		c.disconnect()
		self.assertTrue(fake_socket.close.called)
		self.assertIsNone(c._socket)

	def test_not_connected_read(self):
		c = Cube('127.0.0.1', 62910)
		self.assertRaises(CubeConnectionException, c.read)

	def test_read(self):
		c = Cube('127.0.0.1', 62910)
		c._socket = StaticResponseSocket([
			bytearray('H:', encoding='utf-8') + HelloResponseBytes,
			bytearray('M:', encoding='utf-8') + MResponseBytes
		])
		c.read()
		self.assertEqual(len(c.received_messages), 2)

	def test_read_unknown_response(self):
		c = Cube('127.0.0.1', 62910)
		c._socket = StaticResponseSocket([
			bytearray('X:', encoding='utf-8'),
		])
		c.read()
		self.assertEqual(len(c.received_messages), 0)

	def test_get_message(self):
		c = Cube('127.0.0.1', 62910)
		self.assertFalse(c.get_message(F_RESPONSE))

		c = Cube('127.0.0.1', 62910)
		c.parse_message(F_RESPONSE, b"ntp.homematic.com,ntp.homematic.com")
		msg = FResponse(b"ntp.homematic.com,ntp.homematic.com")
		self.assertEqual(c.get_message(F_RESPONSE), msg)

	def test_double_connect(self):
		c = Cube('127.0.0.1', 62910)
		c._socket = Mock(socket.socket)
		self.assertRaises(CubeConnectionException, c.connect)

	def test_read_after_connect(self):
		c = Cube('127.0.0.1', 62910)
		c.read = Mock()
		c._create_socket = Mock(return_value=Mock(socket.socket))
		c.connect()
		self.assertTrue(c.read.called)

class CubeTest(unittest.TestCase):

	def test_constructor(self):
		c = Cube('1.2.3.4')
		self.assertEqual(c.addr_port, ('1.2.3.4', 62910))

		c = Cube('1.2.3.4', 4567)
		self.assertEqual(c.addr_port, ('1.2.3.4', 4567))

		c = Cube(address='1.2.3.4')
		self.assertEqual(c.addr_port, ('1.2.3.4', 62910))

		c = Cube(address='1.2.3.4', port=9876)
		self.assertEqual(c.addr_port, ('1.2.3.4', 9876))

		c = Cube(DiscoveryNetworkConfigurationResponse(DiscoveryNetworkConfigResponseBytes))
		self.assertEqual(c.addr_port, ('10.10.10.153', 62910))

	def test_context_manager_connect_and_disconnect(self):
		c = Cube((None, None))
		c.connect = Mock()
		c.disconnect = Mock()

		with c:
			self.assertTrue(c.connect.called)

		self.assertTrue(c.disconnect.called)

	def test_context_manager_disconnect_on_exception(self):
		try:
			c = Cube((None, None))
			c.connect = Mock()
			c.disconnect = Mock()
			with c as cube:
				raise Exception("just a test")
		except Exception as ex:
			self.assertTrue(c.connect.called)
			self.assertTrue(c.disconnect.called)
			self.assertEqual(ex.args, ("just a test", ))

	def _mocked_cube(self):
		# conn = Mock()
		# conn.get_message = Mock(return_value=SetResponse(bytearray("00,0,31", encoding='utf-8')))
		c = Cube()
		c._socket = Mock(socket.socket)
		c.send_message = Mock()
		c.get_message = Mock(return_value=SetResponse(bytearray("00,0,31", encoding='utf-8')))
		return c

	def test_set_mode_auto(self):
		c = self._mocked_cube()
		response = c.set_mode_auto(123, '001122')
		c.send_message.assert_called_with(SetTemperatureAndModeMessage('001122', 123, 0x0))
		self.assertIsInstance(response, SetResponse)

	def test_set_mode_boost(self):
		c = self._mocked_cube()
		response = c.set_mode_boost(123, '001122')
		c.send_message.assert_called_with(SetTemperatureAndModeMessage('001122', 123, 0xc0))
		self.assertIsInstance(response, SetResponse)

	def test_set_mode_manual(self):
		c = self._mocked_cube()
		response = c.set_mode_manual(123, '001122', temperature=123)
		c.send_message.assert_called_with(SetTemperatureAndModeMessage('001122', 123, 0x40, temperature=123))
		self.assertIsInstance(response, SetResponse)

	def test_set_mode_vacation(self):
		c = self._mocked_cube()
		response = c.set_mode_vacation(123, '001122', temperature=123, end=datetime.datetime(2015, 12, 16, 12, 00, 00))
		c.send_message.assert_called_with(SetTemperatureAndModeMessage('001122', 123, 0x80, temperature=123, end=datetime.datetime(2015, 12, 16, 12, 00, 00)))
		self.assertIsInstance(response, SetResponse)

	def test_get_ntp_servers(self):
		c = Cube((None, None))
		c._socket = Mock(socket.socket)
		c._socket.recv = Mock(return_value=bytearray())
		c.send_message = Mock()
		self.assertIsNone(c._ntp_servers)
		c.ntp_servers
		c.send_message.assert_called_with(FMessage())
		c.handle_message(FResponse(bytearray("ntp.homematic.com,ntp.homematic.com", encoding='utf-8')))
		self.assertEqual(c._ntp_servers, [u'ntp.homematic.com', u'ntp.homematic.com'])

	def test_get_ntp_servers_no_response(self):
		c = Cube((None, None))
		c._socket = Mock(socket.socket)
		c._socket.recv = Mock(return_value=bytearray("F:ntp.homematic.com,ntp.homematic.com", encoding='utf-8'))
		c.send_message = Mock()
		self.assertIsNone(c._ntp_servers)
		c.ntp_servers
		c.send_message.assert_called_with(FMessage())
		self.assertIsNone(c.ntp_servers)

	def test_set_ntp_servers(self):
		c = self._mocked_cube()
		c.ntp_servers = ['foo', 'bar']
		c.send_message.assert_called_with(FMessage(['foo', 'bar']))

	def test_rooms_no_messages(self):
		c = self._mocked_cube()
		c.get_message = Mock(return_value=None)
		self.assertEqual(c.rooms, [])

	def test_rooms(self):
		c = Cube()
		c.get_message = Mock(return_value=MResponse([MResponseBytes]))
		self.assertEqual(c.rooms, [
			Room(room_id=1, name='Wohnzimmer', rf_address='122B65', devices=[
				Device(rf_address='122B65', serial='MEQ1472997', name='Heizung'),
			])
		])

	def test_set_program(self):
		c = self._mocked_cube()
		response = c.set_program(1, '122b56', 1, [])
		c.send_message.assert_called_with(SetProgramMessage('122b56', 1, 1, []))
		self.assertIsInstance(response, SetResponse)

	def test_set_temperatures(self):
		c = self._mocked_cube()
		response = c.set_temperatures(1, '122b56', 1, 2, 3, 4, 5, 6, 7)
		c.send_message.assert_called_with(SetTemperaturesMessage('122b56', 1, 1, 2, 3, 4, 5, 6, 7))
		self.assertIsInstance(response, SetResponse)

	def test_set_valve_config(self):
		c = self._mocked_cube()
		response = c.set_valve_config(1, '122b56', 10, 0.5, 0, 1, 10)
		c.send_message.assert_called_with(SetValveConfigMessage('122b56', 1, 10, 0.5, 0, 1, 10))
		self.assertIsInstance(response, SetResponse)

	def test_handle_message(self):
		c = Cube(None, None)

		msg = HelloResponse(HelloResponseBytes)
		c.handle_message(msg)
		self.assertEqual(c.info, msg)

		msg = FResponse(b"ntp.homematic.com,ntp.homematic.com")
		c.handle_message(msg)
		self.assertEqual(c._ntp_servers, ['ntp.homematic.com', 'ntp.homematic.com'])

		msg = MResponse(MResponseBytes)
		c.handle_message(msg)
		self.assertEqual(c.devices, [
			Device(rf_address='122B65', serial='MEQ1472997', name='Heizung', room_id=1, device_type=2),
		])

		c = Cube(None, None)
		c._devices = DeviceList([
			Device(rf_address='122B65', serial='MEQ1472997', name='Heizung', room_id=2, device_type=2),
		])
		msg = MResponse(MResponseBytes)
		c.handle_message(msg)
		self.assertEqual(c.devices, [
			Device(rf_address='122B65', serial='MEQ1472997', name='Heizung', room_id=1, device_type=2),
		])

		msg = ConfigurationResponse(ThermostatConfigurationBytes)
		c.handle_message(msg)
		self.assertEqual(c.devices, [
			Device(rf_address='122B65', serial='MEQ1472997', name='Heizung', room_id=1, configuration=msg, device_type=2),
		])

		c = Cube(None, None)
		c._devices = DeviceList([
			Device(rf_address='122B65', serial='MEQ1472997', name='Heizung', room_id=1),
		])
		lresp = LResponse("BhIrZfcSGWQ8AOsA")
		c.handle_message(lresp)
		self.assertEqual(c.devices, [
			Device(rf_address='122B65', serial='MEQ1472997', name='Heizung', room_id=1, settings=lresp),
		])
		msg = ConfigurationResponse(ThermostatConfigurationBytes)
		c.handle_message(msg)
		self.assertEqual(c.devices, [
			Device(rf_address='122B65', serial='MEQ1472997', name='Heizung', room_id=1, configuration=msg, settings=lresp),
		])
