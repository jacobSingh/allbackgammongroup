import logging
import os

logging.basicConfig(filename='/tmp/perf.log', format='%(asctime)s - %(name)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s')
l = logging.getLogger("abg")
if ("ABG_LOG_LEVEL" in os.environ):
    level = os.environ["ABG_LOG_LEVEL"]
else:
    level = logging.INFO

l.setLevel(level)

ch = logging.StreamHandler()
ch.setLevel(level)
l.addHandler(ch)


l.error("START")
# -*- coding: utf-8 -*-
"""Create an application instance."""
from flask.helpers import get_debug_flag

from abg_stats.app import create_app
from abg_stats.settings import DevConfig, ProdConfig
l.error("after loading settings")

CONFIG = DevConfig if get_debug_flag() else ProdConfig
l.error("Before loading the app")
app = create_app(CONFIG)
l.error("After loading the app")
