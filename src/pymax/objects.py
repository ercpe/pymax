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

	def __init__(self, byte_tuple_string):
		if byte_tuple_string is None or not byte_tuple_string:
			raise ValueError

		if isinstance(byte_tuple_string, bytearray):
			if len(byte_tuple_string) != 3:
				raise ValueError("Need exactly 3 bytes when passing a bytearray")
			self._bytes = byte_tuple_string
		elif isinstance(byte_tuple_string, tuple):
			if len(byte_tuple_string) != 3:
				raise ValueError("Need exactly 3 elements when passing a tuple")
			self._bytes = bytearray(list(byte_tuple_string))
		else:
			if len(byte_tuple_string) != 6:
				raise ValueError("Need a string of length 6 passing a string")
			self._bytes = bytearray([int(byte_tuple_string[s:s + 2], 16) for s in range(0, 6, 2)])

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
		return filter(lambda d: getattr(d, 'room_id', None) == room_id, self)

	def __contains__(self, item):
		if isinstance(item, str):
			return len(list(filter(lambda d: d.name == item, self))) > 0
		elif isinstance(item, RFAddr) or isinstance(item, bytearray):
			return len(list(filter(lambda d: d.rf_address == item, self))) > 0
		return False

	def get(self, **kwargs):
		if not kwargs:
			return None

		for item in self:
			if all((item.get(k, None) == v for k, v in kwargs.items())):
				return item

	def update(self, **kwargs):
		instance = self.get(**dict(((k, v) for k, v in kwargs.items() if k in ('rf_address', 'serial', 'name'))))

		if instance:
			for k, v in kwargs.items():
				instance[k] = v
		else:
			return self.append(Device(**kwargs))


class Device(dict):

	def __getattr__(self, item):
		if item in self:
			return self[item]
		raise AttributeError("%s has no attribute %s" % (self.__class__.__name__, item))

	def __eq__(self, other):
		if isinstance(other, dict) or isinstance(other, Device):
			return len(self) == len(other) and all((k in other for k in self.keys())) and \
				all((self[k] == other[k] for k in self.keys()))
		return False

	def __repr__(self):
		return self.__str__()

	def __str__(self):
		return "%s(%s)" % (self.__class__.__name__, ', '.join(["%s=%s" % (k, self[k]) for k in sorted(self.keys())]))
