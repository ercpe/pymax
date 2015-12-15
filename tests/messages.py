# -*- coding: utf-8 -*-

import unittest

from pymax.messages import QuitMessage, FMessage


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
