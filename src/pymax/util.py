# -*- coding: utf-8 -*-

import logging

import datetime

import struct

logger = logging.getLogger(__name__)

class Debugger(object): # pragma: nocover
	def dump_bytes(self, barray, message=None, level=logging.DEBUG):
		if not logger.isEnabledFor(level):
			return

		if isinstance(barray, bytearray):
			logger.log(level, "%s (%s bytes)", (message or 'Data'), len(barray))
			for row_num in range(0, len(barray), 10):
				row_bytes = barray[row_num:row_num+10]
				logger.log(level, "%s  %s" % (str(row_num).ljust(2), ' '.join(["%02x" % x for x in row_bytes])))
				logger.log(level, "     %s" % '  '.join([chr(x) if 32 < x < 128 else ' ' for x in row_bytes]))

			#logger.log(level, ', '.join(["0x%02X" % x for x in barray]))


# hex:  9d 0b
# 	         +-++++--------------- day: 1 1101 -> 29
#            | ||||
# dual: | 1001 1101 | 0000 1011 | (9D0B)
#         |||          | | ||||
#         |||          | +-++++--- year: 0 1011 -> 11 = year - 2000
#         |||          |                 (to get the actual year, 2000 must be added to the value: 11+2000 = 2011)
#         |||          |
#         +++----------+---------- month: 1000 -> 8

def date_to_dateuntil(date):
	if date.year < 2000:
		raise ValueError("Cannot store dates before 2000-01-01 as dateuntil")
	a = b = 0

	b = date.year - 2000
	a = date.day

	m = date.month
	a |= m >> 1 << 5

	if m & 0x01:
		b |= 0x40

	return bytearray([a, b])


def dateuntil_to_date(date_until):
	a, b = date_until

	year = b - (b >> 4 << 4)

	month = a >> 5 << 1
	if b & 0x40:
		month |= 0x01

	day = a - (a >> 5 << 5)

	return datetime.date(year+2000, month, day)

def unpack_temp_and_time(temp_and_time):
	a, b = tuple(temp_and_time)

	temperature = (a >> 1) / 2.0

	minutes = b + ((a & 0x01) * 256)
	minutes *= 5

	return temperature, minutes

def pack_temp_and_time(temperature, time):
	temp = int(temperature * 2.0)
	temp <<= 9

	if isinstance(time, int):
		# time = minutes
		minutes = int(time / 5.0)
	else:
		# time => datetime.time()
		minutes = int(((time.hour * 60) + time.minute) / 5)

	return bytearray(struct.pack(">H", temp | minutes))

def cube_day_to_py_day(day):
	if day <= 1:
		return 5 + day
	return day - 2

def py_day_to_cube_day(day):
	d = day + 2
	if d >= 7:
		return d - 7
	return d
