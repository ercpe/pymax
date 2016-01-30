# -*- coding: utf-8 -*-
import unittest
import datetime

from pymax.objects import ProgramSchedule
from pymax.response import DiscoveryIdentifyResponse, BaseResponse, DiscoveryNetworkConfigurationResponse, \
	HelloResponse, \
	MResponse, ConfigurationResponse, DeviceCube, DeviceRadiatorThermostatPlus, LResponse, FResponse, SetResponse

DiscoveryIdentifyRequestBytes = bytearray([
	0x65, 0x51, 0x33, 0x4D, 0x61, 0x78, 0x2A, 0x00, 0x2A, 0x2A, 0x2A, 0x2A, 0x2A, 0x2A, 0x2A, 0x2A, 0x2A, 0x2A, 0x49
])

DiscoveryNetworkConfigRequestBytes = bytearray([
	0x65, 0x51, 0x33, 0x4D, 0x61, 0x78, 0x2A, 0x00, 0x4B, 0x45, 0x51, 0x30, 0x35, 0x32, 0x33, 0x38, 0x36, 0x34, 0x4E
])

DiscoveryIdentifyResponseBytes = bytearray([
	0x65, 0x51, 0x33, 0x4D, 0x61, 0x78, 0x41, 0x70,
	0x4B, 0x45, 0x51, 0x30, 0x35, 0x32, 0x33, 0x38, 0x36, 0x34,
	0x3E,
	0x49,
	0x00, 0x09, 0x7F, 0x2C,
	0x01, 0x13])

DiscoveryNetworkConfigResponseBytes = bytearray([
	0x65, 0x51, 0x33, 0x4d, 0x61, 0x78, 0x41, 0x70,
	0x4B, 0x45, 0x51, 0x30, 0x35, 0x32, 0x33, 0x38, 0x36, 0x34,
	0x3e,
	0x4e,
	0x0a, 0x0a, 0x0a, 0x99,
	0x0a, 0x0a, 0x0a, 0x01,
	0xff, 0xff, 0xff, 0x00,
	0x0a, 0x0a, 0x0a, 0x01,
	0x00, 0x00, 0x00, 0x00
])

HelloResponseBytes = bytearray([
	0x4B, 0x45, 0x51, 0x30, 0x35, 0x32, 0x33, 0x38, 0x36, 0x34, 0x2C,
	0x31, 0x30, 0x62, 0x31, 0x39, 0x39, 0x2C,
	0x30, 0x31, 0x31, 0x33, 0x2C,
	0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x2C,
	0x35, 0x34, 0x32, 0x34, 0x33, 0x63, 0x64, 0x64, 0x2C,
	0x30, 0x30, 0x2C,
	0x33, 0x32, 0x2C,
	0x30, 0x66, 0x30, 0x63, 0x30, 0x64, 0x2C,
	0x30, 0x38, 0x31, 0x32, 0x2C,
	0x30, 0x33, 0x2C,
	0x30, 0x30, 0x30, 0x30
])

MResponseBytes = bytearray([
	0x30, 0x30, 0x2C,
	0x30, 0x31, 0x2C,
	0x56, 0x67, 0x49, 0x42, 0x41, 0x51, 0x70, 0x58, 0x62, 0x32, 0x68, 0x75,
	0x65, 0x6D, 0x6C, 0x74, 0x62, 0x57, 0x56, 0x79, 0x45, 0x69, 0x74, 0x6C,
	0x41, 0x51, 0x49, 0x53, 0x4B, 0x32, 0x56, 0x4E, 0x52, 0x56, 0x45, 0x78,
	0x4E, 0x44, 0x63, 0x79, 0x4F, 0x54, 0x6B, 0x33, 0x42, 0x30, 0x68, 0x6C,
	0x61, 0x58, 0x70, 0x31, 0x62, 0x6D, 0x63, 0x42, 0x41, 0x51, 0x3D, 0x3D
])

CubeConfigurationBytes = bytearray(b'10b199,7RCxmQATAf9MRVExMTU0NzI3AAsABEAAAAAAAAAAAP///////////////////////////'
								   b'wsABEAAAAAAAAAAQf///////////////////////////2h0dHA6Ly9tYXguZXEtMy5kZTo4MC9jdW'
								   b'JlADAvbG9va3VwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'
								   b'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAENFVAAACgADAAAOEE'
								   b'NFU1QAAwACAAAcIA==')
ThermostatConfigurationBytes = bytearray(b'122b65,0hIrZQIBEABNRVExNDcyOTk3Oyc9CQcYA5IM/wBESHkPRSBFIEUgRSBFIEUgRSBFIEUg'
										 b'RSBFIERIeQlFIEUgRSBFIEUgRSBFIEUgRSBFIEUgREJ4XkTJeRJFIEUgRSBFIEUgRSBFIEUgRSB'
										 b'EQnheRMl5EkUgRSBFIEUgRSBFIEUgRSBFIERCeF5EyXkSRSBFIEUgRSBFIEUgRSBFIEUgREJ4Xk'
										 b'TJeRJFIEUgRSBFIEUgRSBFIEUgRSBEQnheRMl5EkUgRSBFIEUgRSBFIEUgRSBFIA==')


class BaseResponseTest(unittest.TestCase):
	def test_fix_length(self):
		class FixedLengthResponse(BaseResponse):
			length = 5

			def _parse(self):
				pass

		self.assertRaises(ValueError, FixedLengthResponse, None)  # empty
		self.assertRaises(ValueError, FixedLengthResponse, bytearray())  # empty
		self.assertRaises(ValueError, FixedLengthResponse, bytearray([0]))  # too short
		self.assertRaises(ValueError, FixedLengthResponse, bytearray([0, 0]))  # too short
		self.assertRaises(ValueError, FixedLengthResponse, bytearray([0 for _ in range(0, 100)]))  # too long

	def test_min_length(self):
		class MinLengthResponse(BaseResponse):
			min_length = 5

			def _parse(self):
				pass

		self.assertRaises(ValueError, MinLengthResponse, None)  # empty
		self.assertRaises(ValueError, MinLengthResponse, bytearray())  # empty
		self.assertRaises(ValueError, MinLengthResponse, bytearray([0]))  # too short

	def test_max_length(self):
		class MaxLengthResponse(BaseResponse):
			max_length = 5

			def _parse(self):
				pass

		self.assertRaises(ValueError, MaxLengthResponse, None)  # empty
		self.assertRaises(ValueError, MaxLengthResponse, bytearray())  # empty
		self.assertRaises(ValueError, MaxLengthResponse, bytearray([0 for _ in range(0, 100)]))  # too long

	def test_bytes_to_int(self):
		class FakeResponse(BaseResponse):
			def _parse(self):
				pass

		r = FakeResponse(bytearray([0x00]))
		self.assertEqual(r.bytes_to_int(None), None)
		self.assertEqual(r.bytes_to_int(bytearray([])), None)
		self.assertEqual(r.bytes_to_int(bytearray([0x00])), 0)
		self.assertEqual(r.bytes_to_int(bytearray([0x0a, 0x01])), 11)


class DiscoveryIdentifyResponseTest(unittest.TestCase):
	def test_parsing(self):
		response = DiscoveryIdentifyResponse(DiscoveryIdentifyResponseBytes)
		self.assertEqual(response.name, 'eQ3MaxAp')
		self.assertEqual(response.serial, 'KEQ0523864')
		self.assertEqual(response.request_id, '>')
		self.assertEqual(response.request_type, 'I')
		self.assertEqual(response.rf_address, '097f2c')
		self.assertEqual(response.fw_version, '0113')

	def test_str(self):
		response = DiscoveryIdentifyResponse(DiscoveryIdentifyResponseBytes)
		self.assertEqual(str(response), "KEQ0523864: RF addr: 097f2c, FW version: 0113")


class DiscoveryNetworkConfigResponseTest(unittest.TestCase):

	def test_parsing(self):
		response = DiscoveryNetworkConfigurationResponse(DiscoveryNetworkConfigResponseBytes)
		self.assertEqual(response.name, 'eQ3MaxAp')
		self.assertEqual(response.serial, 'KEQ0523864')
		self.assertEqual(response.request_id, '>')
		self.assertEqual(response.request_type, 'N')
		self.assertEqual(response.ip_address, '10.10.10.153')
		self.assertEqual(response.netmask, '255.255.255.0')
		self.assertEqual(response.gateway, '10.10.10.1')
		self.assertEqual(response.dns1, '10.10.10.1')
		self.assertEqual(response.dns2, '0.0.0.0')


class HelloResponseTest(unittest.TestCase):
	def test_parsing(self):
		response = HelloResponse(HelloResponseBytes)
		self.assertEqual(response.serial, 'KEQ0523864')
		self.assertEqual(response.rf_address, '10b199')
		self.assertEqual(response.fw_version, '0113')
		self.assertEqual(response.datetime, datetime.datetime(2015, 12, 13, 8, 18, 0))

	def test_str(self):
		response = HelloResponse(HelloResponseBytes)
		self.assertEqual(str(response), "KEQ0523864: RF addr: 10b199, FW: 0113, Date: 2015-12-13 08:18:00")


class MResponseTest(unittest.TestCase):
	def _make_multi_response(self):
		b1 = bytearray([
			0x30, 0x30, 0x2C,
			0x30, 0x32, 0x2C,
			0x56, 0x67, 0x49, 0x42, 0x41, 0x51, 0x70, 0x58, 0x62, 0x32, 0x68, 0x75,
			0x65, 0x6D, 0x6C, 0x74, 0x62, 0x57, 0x56, 0x79, 0x45, 0x69, 0x74, 0x6C,
		])
		b2 = bytearray([
			0x30, 0x31, 0x2C,
			0x30, 0x32, 0x2C,
			0x41, 0x51, 0x49, 0x53, 0x4B, 0x32, 0x56, 0x4E, 0x52, 0x56, 0x45, 0x78,
			0x4E, 0x44, 0x63, 0x79, 0x4F, 0x54, 0x6B, 0x33, 0x42, 0x30, 0x68, 0x6C,
			0x61, 0x58, 0x70, 0x31, 0x62, 0x6D, 0x63, 0x42, 0x41, 0x51, 0x3D, 0x3D
		])

		return MResponse([b1, b2])

	def test_parsing(self):
		response = MResponse([MResponseBytes])

		self.assertEqual(response.num_rooms, 1)
		self.assertEqual(response.rooms, [
			(1, 'Wohnzimmer', '122B65')
		])
		self.assertEqual(response.num_devices, 1)
		self.assertEqual(response.devices, [
			(0, 2, '122B65', 'MEQ1472997', 'Heizung', 1)
		])

		response = MResponse(bytearray('00,01,VgIBAQ9TbGFhcGthbWVyIExpc2EAAAABAxIXB01FUTA4NTM2MDMRd2FuZHRoZXJtb3N0YWF0IDEBAQ==', 'utf-8'))
		self.assertEqual(response.num_rooms, 1)
		self.assertEqual(response.num_devices, 1)
		self.assertEqual(response.devices, [
			(0, 3, '121707', 'MEQ0853603', 'wandthermostaat 1', 1)
		])

	def test_multi_parsing(self):
		response = self._make_multi_response()

		self.assertEqual(response.num_rooms, 1)
		self.assertEqual(response.rooms, [
			(1, 'Wohnzimmer', '122B65')
		])
		self.assertEqual(response.num_devices, 1)
		self.assertEqual(response.devices, [
			(0, 2, '122B65', 'MEQ1472997', 'Heizung', 1)
		])


class ConfigurationResponseTest(unittest.TestCase):
	def test_cube_config(self):
		response = ConfigurationResponse(CubeConfigurationBytes)

		self.assertEqual(response.device_type, DeviceCube)
		self.assertEqual(response.device_addr, '10B199')
		self.assertEqual(response.serial_number, 'LEQ115472')
		self.assertEqual(response.portal_enabled, False)
		self.assertEqual(response.portal_url, 'http://max.eq-3.de:80/cube')

	def test_thermostat_config(self):
		response = ConfigurationResponse(ThermostatConfigurationBytes)

		self.assertEqual(response.device_type, DeviceRadiatorThermostatPlus)
		self.assertEqual(response.device_addr, '122B65')
		self.assertEqual(response.serial_number, 'MEQ147299')
		self.assertEqual(response.comfort_temperature, 29.5)
		self.assertEqual(response.eco_temperature, 19.5)
		self.assertEqual(response.max_set_point_temperature, 30.5)
		self.assertEqual(response.min_set_point_temperature, 4.5)
		self.assertEqual(response.temperature_offset, 0.0)
		self.assertEqual(response.window_open_temperature, 12.0)
		self.assertEqual(response.window_open_duration, 15.0)
		self.assertEqual(response.boost_duration, 20.0)
		self.assertEqual(response.boost_valve_setting, 90.0)
		self.assertEqual(response.decalcification_day, 0)
		self.assertEqual(response.decalcification_hour, 12)
		self.assertEqual(response.max_valve_setting, 100)

		self.assertTrue(len(response.week_program) > 0)

		self.assertEqual(response.week_program, [
			[
				ProgramSchedule(17.0, datetime.time(0, 0), datetime.time(6, 0)),
				ProgramSchedule(30.0, datetime.time(6, 0), datetime.time(22, 35)),
				ProgramSchedule(17.0, datetime.time(22, 35), 1440),
			],
			[
				ProgramSchedule(17.0, datetime.time(0, 0), datetime.time(6, 0)),
				ProgramSchedule(30.0, datetime.time(6, 0), datetime.time(22, 5)),
				ProgramSchedule(17.0, datetime.time(22, 5), 1440),
			],
			[
				ProgramSchedule(17.0, datetime.time(0, 0), datetime.time(5, 30)),
				ProgramSchedule(30.0, datetime.time(5, 30), datetime.time(7, 50)),
				ProgramSchedule(17.0, datetime.time(7, 50), datetime.time(16, 45)),
				ProgramSchedule(30.0, datetime.time(16, 45), datetime.time(22, 50)),
				ProgramSchedule(17.0, datetime.time(22, 50), 1440),
			],
			[
				ProgramSchedule(17.0, datetime.time(0, 0), datetime.time(5, 30)),
				ProgramSchedule(30.0, datetime.time(5, 30), datetime.time(7, 50)),
				ProgramSchedule(17.0, datetime.time(7, 50), datetime.time(16, 45)),
				ProgramSchedule(30.0, datetime.time(16, 45), datetime.time(22, 50)),
				ProgramSchedule(17.0, datetime.time(22, 50), 1440),
			],
			[
				ProgramSchedule(17.0, datetime.time(0, 0), datetime.time(5, 30)),
				ProgramSchedule(30.0, datetime.time(5, 30), datetime.time(7, 50)),
				ProgramSchedule(17.0, datetime.time(7, 50), datetime.time(16, 45)),
				ProgramSchedule(30.0, datetime.time(16, 45), datetime.time(22, 50)),
				ProgramSchedule(17.0, datetime.time(22, 50), 1440),
			],
			[
				ProgramSchedule(17.0, datetime.time(0, 0), datetime.time(5, 30)),
				ProgramSchedule(30.0, datetime.time(5, 30), datetime.time(7, 50)),
				ProgramSchedule(17.0, datetime.time(7, 50), datetime.time(16, 45)),
				ProgramSchedule(30.0, datetime.time(16, 45), datetime.time(22, 50)),
				ProgramSchedule(17.0, datetime.time(22, 50), 1440),
			],
			[
				ProgramSchedule(17.0, datetime.time(0, 0), datetime.time(5, 30)),
				ProgramSchedule(30.0, datetime.time(5, 30), datetime.time(7, 50)),
				ProgramSchedule(17.0, datetime.time(7, 50), datetime.time(16, 45)),
				ProgramSchedule(30.0, datetime.time(16, 45), datetime.time(22, 50)),
				ProgramSchedule(17.0, datetime.time(22, 50), 1440),
			],
		])


class LResponseTest(unittest.TestCase):
	def test_parsing(self):
		response = LResponse("BhIrZfcSGWQ8AOsA")

		self.assertEqual(response.rf_addr, '122b65')
		self.assertFalse(response.weekly_program)
		self.assertTrue(response.manual_program)
		self.assertFalse(response.vacation_program)
		self.assertFalse(response.boost_program)

		self.assertTrue(response.dst_active)
		self.assertTrue(response.gateway_known)
		self.assertFalse(response.panel_locked)
		self.assertTrue(response.link_ok)
		self.assertFalse(response.battery_low)

		self.assertTrue(response.status_initialized)
		self.assertFalse(response.is_answer)
		self.assertFalse(response.is_error)
		self.assertFalse(response.is_valid)

	def test_parsing_with_extra_fields(self):
		response = LResponse("CxIrZfcSGWQ8AOsF")

		self.assertEqual(response.rf_addr, '122b65')
		self.assertFalse(response.weekly_program)
		self.assertTrue(response.manual_program)
		self.assertFalse(response.vacation_program)
		self.assertFalse(response.boost_program)
		self.assertEqual(response.valve_position, 100)
		self.assertEqual(response.temperature, 30.0)
		self.assertEqual(response.time_until, datetime.timedelta(hours=2, minutes=30))

		self.assertTrue(response.dst_active)
		self.assertTrue(response.gateway_known)
		self.assertFalse(response.panel_locked)
		self.assertTrue(response.link_ok)
		self.assertFalse(response.battery_low)

		self.assertTrue(response.status_initialized)
		self.assertFalse(response.is_answer)
		self.assertFalse(response.is_error)
		self.assertFalse(response.is_valid)


class FResponseTest(unittest.TestCase):
	def test_parsing(self):
		response = FResponse(bytearray("ntp.homematic.com,ntp.homematic.com", encoding='utf-8'))
		self.assertEqual(response.ntp_servers, [
			'ntp.homematic.com',
			'ntp.homematic.com'
		])


class SetResponseTest(unittest.TestCase):
	def test_parsing(self):
		response = SetResponse(bytearray("00,0,31", encoding='utf-8'))

		self.assertEqual(response.duty_cycle, 0)
		self.assertEqual(response.command_result, 0)
		self.assertTrue(response.command_success)
		self.assertEqual(response.free_mem_slots, 49)
