# -*- coding: utf-8 -*-

QUIT_MESSAGE = 'q'
F_MESSAGE = 'f'

class BaseMessage(object):

	def __init__(self, msg):
		self.msg = msg

	def to_bytes(self):
		data = (self.msg + ':').encode('utf-8')

		payload = self.get_payload()
		if payload:
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