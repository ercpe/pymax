# -*- coding: utf-8 -*-

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from response import *
from messages import *
from cube import *
from util import *
from objects import *

import logging
logging.basicConfig(
    level=logging.CRITICAL,
    format='%(asctime)s %(levelname)-7s %(message)s',
)

if __name__ == '__main__':
    unittest.main()
