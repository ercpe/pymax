# -*- coding: utf-8 -*-
import unittest

from pymax.cube import Connection
from pymax.response import HELLO_RESPONSE, HelloResponse, M_RESPONSE, MResponse
from response import HelloResponseBytes, MResponseBytes


class ConnectionTest(unittest.TestCase):

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
