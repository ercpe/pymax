# -*- coding: utf-8 -*-
import base64

from pymax.util import date_to_dateuntil

QUIT_MESSAGE = 'q'
F_MESSAGE = 'f'
S_MESSAGE = 's'

class BaseMessage(object):

	base64payload = False

	def __init__(self, msg):
		self.msg = msg

	def to_bytes(self):
		data = (self.msg + ':').encode('utf-8')

		payload = self.get_payload()
		if payload:
			if self.base64payload:
				data += base64.b64encode(payload)
			else:
				data += payload

		data += bytearray(b"\r\n")
		return data

	def get_payload(self):
		return None


class QuitMessage(BaseMessage):

	def __init__(self):
		super(QuitMessage, self).__init__(QUIT_MESSAGE)


class FMessage(BaseMessage):
	def __init__(self, ntp_servers=None):
		super(FMessage, self).__init__(F_MESSAGE)
		self.ntp_servers = ntp_servers

	def get_payload(self):
		s = ','.join((x.strip() for x in self.ntp_servers or []))
		return bytearray(s, 'utf-8')

	def __eq__(self, other):
		return isinstance(other, FMessage) and self.ntp_servers == other.ntp_servers


class SetMessage(BaseMessage):
	base64payload = True

	TemperatureAndMode = [0x00, 0x04, 0x40, 0x00, 0x00, 0x00] # b'000440000000'

	def __init__(self, type, rf_addr, room_number):
		super(SetMessage, self).__init__(S_MESSAGE)
		self.rf_addr = rf_addr
		self.type = type
		self.room_number = room_number

	def get_payload(self):
		return bytearray(self.type) + bytearray([
			int(self.rf_addr[0:2], 16),
			int(self.rf_addr[2:4], 16),
			int(self.rf_addr[4:6], 16)
		]) + bytearray([self.room_number])


class SetTemperatureAndModeMessage(SetMessage):
	ModeAuto = 0x0
	ModeManual = 0x40
	ModeVacation = 0x80
	ModeBoost = 0xc0

	def __init__(self, rf_addr, room_number, mode, **kwargs):
		super(SetTemperatureAndModeMessage, self).__init__(SetMessage.TemperatureAndMode, rf_addr, room_number)
		self.mode = mode
		self.temperature = kwargs.get('temperature', 0)
		self.end = kwargs.get('end', None)

	def get_payload(self):
		x = int(self.temperature * 2)
		x |= self.mode

		payload = super(SetTemperatureAndModeMessage, self).get_payload() + bytearray([x])

		if self.end:
			payload += date_to_dateuntil(self.end.date())
			payload += bytearray([(self.end.time().hour * 2) + (1 if self.end.time().minute >= 30 else 0)])

		return payload

	def __str__(self):
		return "%s(mode=%s, temperature=%s, end=%s)" % (self.__class__.__name__, self.mode, self.temperature, self.end)

	def __repr__(self):
		return self.__str__()

	def __eq__(self, other):
		return isinstance(other, SetTemperatureAndModeMessage) and \
				self.mode == other.mode and \
				self.temperature == other.temperature and \
				self.end == other.end