# -*- coding: utf-8 -*-

QUIT_MESSAGE = 'q'


class BaseMessage(object):

	def __init__(self, msg):
		self.msg = msg

	def to_bytes(self):
		data = (self.msg + ':').encode('utf-8')

		payload = self.get_payload()
		if payload:
			data += bytearray(payload)

		data += bytearray(b"\r\n")
		return data

	def get_payload(self):
		return None


class QuitMessage(BaseMessage):

	def __init__(self):
		super(QuitMessage, self).__init__(QUIT_MESSAGE)
