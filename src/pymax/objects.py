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


class DeviceList(list):

	def __init__(self, iterable=None):
		super(DeviceList, self).__init__(iterable or [])

	def for_room(self, room_id):
		return filter(lambda d: d.room_id == room_id, self)


DeviceType = collections.namedtuple('Device', ('rf_address', 'serial', 'name'))
class Device(DeviceType):
	def __new__(cls, **kwargs):
		for f in DeviceType._fields:
			kwargs.setdefault(f, None)
		super(Device, cls).__new__(cls, **kwargs)
