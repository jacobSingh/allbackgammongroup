
import logging
import pandas as pd
import os

logging.basicConfig(filename='/tmp/abg.log', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
l = logging.getLogger("abg")
if ("ABG_LOG_LEVEL" in os.environ):
    level = os.environ["ABG_LOG_LEVEL"]
else:
    level = logging.INFO

l.setLevel(level)

ch = logging.StreamHandler()
ch.setLevel(level)
l.addHandler(ch)

## Surpresses annoying errors
pd.options.mode.chained_assignment = None
