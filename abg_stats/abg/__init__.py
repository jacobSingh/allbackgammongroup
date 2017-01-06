import logging
l = logging.getLogger("abg")
# -*- coding: utf-8 -*-
"""The abg module."""
l.error("Player")
from .views import player # noqa
l.error("Other")
from .views import other  # noqa
l.error("Tournaments")
from .views import tournaments  # noqa
l.error("Done")
