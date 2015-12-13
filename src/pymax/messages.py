# -*- coding: utf-8 -*-

QUIT_MESSAGE = 'q'


class BaseMessage(object):

	def __init__(self, msg, payload=None):
		self.msg = msg
		self.payload = payload

	def to_bytes(self):
		data = (self.msg + ':').encode('utf-8')
		if self.payload:
			data += bytearray(self.payload)
		data += bytearray(b"\r\n")
		return data


class QuitMessage(BaseMessage):

	def __init__(self):
		super(QuitMessage, self).__init__(QUIT_MESSAGE)
