# -*- coding: utf-8 -*-

import unittest

from pymax.messages import QuitMessage

class QuitMessageTest(unittest.TestCase):

	def test_bytes(self):
		m = QuitMessage()
		self.assertEqual(m.to_bytes(), bytearray(b'q:\r\n'))
