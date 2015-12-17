# -*- coding: utf-8 -*-
import collections
import datetime

class ProgramSchedule(object):

	def __init__(self, temperature, begin, end):
		def _minutes_to_time(t):
			if t >= 1440:
				return datetime.time()
			hours = int(t / 60.0)
			minutes = t - int(hours * 60)
			return datetime.time(hour=hours, minute=minutes)

		self.temperature = temperature

		if isinstance(begin, int):
			self.begin_time = _minutes_to_time(begin)
		else:
			self.begin_time = begin

		if isinstance(end, int):
			self.end_time = _minutes_to_time(end)
		else:
			self.end_time = end

	def __eq__(self, other):
		return isinstance(other, ProgramSchedule) and self.temperature == other.temperature and \
			self.begin_time == other.begin_time and self.end_time == other.end_time

	def __repr__(self):
		return "%s(temperature=%s, start=%s, end=%s)" % (
			self.__class__.__name__, self.temperature, self.begin_time, self.end_time
		)