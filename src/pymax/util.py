# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger(__name__)

class Debugger(object):
	def dump_bytes(self, barray, message=None, level=logging.DEBUG):
		if not logger.isEnabledFor(level):
			return

		logger.log(level, "%s (%s bytes)" % (message or 'Data', len(barray)))

		for row_num in range(0, len(barray), 10):
			row_bytes = barray[row_num:row_num+10]
			logger.log(level, "%s  %s" % (str(row_num).ljust(2), ' '.join(["%02x" % x for x in row_bytes])))
			logger.log(level, "     %s" % '  '.join([chr(x) if 32 < x < 128 else ' ' for x in row_bytes]))

		#logger.log(level, ', '.join(["0x%X" % x for x in barray]))