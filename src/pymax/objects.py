# -*- coding: utf-8 -*-
import collections
import datetime

class ProgramSchedule(object):

	def __init__(self, temperature, begin, end):
		self.temperature = temperature
		if begin.__class__ == datetime.time:
			self.begin_minutes = (begin.hour * 60) + begin.minute
		else:
			self.begin_minutes = begin

		if end.__class__ == datetime.time:
			self.end_minutes = (end.hour * 60) + end.minute
		else:
			self.end_minutes = end

	def __eq__(self, other):
		return isinstance(other, ProgramSchedule) and self.temperature == other.temperature and \
			self.begin_minutes == other.begin_minutes and self.end_minutes == other.end_minutes

	def __repr__(self):
		return "%s(temperature=%s, start=%s, end=%s)" % (
			self.__class__.__name__, self.temperature, self.begin_minutes, self.end_minutes
		)


class RFAddr(object):

	def __init__(self, bytes_or_string):
		if bytes_or_string is None or not bytes_or_string:
			raise ValueError

		if isinstance(bytes_or_string, bytearray):
			if len(bytes_or_string) != 3:
				raise ValueError("Need exactly 3 bytes when passing a bytearray")
			self._bytes = bytes_or_string
		else:
			if len(bytes_or_string) != 6:
				raise ValueError("Need a string of length 6 passing a string")
			self._bytes = bytearray([int(bytes_or_string[s:s+2], 16) for s in range(0, 6, 2)])

	def __eq__(self, other):
		if isinstance(other, str):
			return self.__str__().lower() == other.lower()
		elif isinstance(other, RFAddr):
			return self._bytes == other._bytes
		elif isinstance(other, bytearray):
			return self._bytes == other

	def __repr__(self):
		return self.__str__()

	def __str__(self):
		return "{0:02x}{1:02x}{2:02x}".format(*self._bytes)


class DeviceList(list):

	def __init__(self, iterable=None):
		super(DeviceList, self).__init__(iterable or [])

	def for_room(self, room_id):
		return filter(lambda d: d.room_id == room_id, self)

	def __contains__(self, item):
		if isinstance(item, str):
			return len(filter(lambda d: d.name == item, self)) > 0
		elif isinstance(item, RFAddr):
			return len(filter(lambda d: d.rf_address == item, self)) > 0
		return False

DeviceType = collections.namedtuple('Device', ('rf_address', 'serial', 'name'))

class Device(DeviceType):

	def __new__(cls, **kwargs):
		for f in DeviceType._fields:
			kwargs.setdefault(f, None)
		super(Device, cls).__new__(cls, **kwargs)
