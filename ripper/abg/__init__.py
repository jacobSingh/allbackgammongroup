
import logging
import pandas as pd

logging.basicConfig(filename='/tmp/abg.log', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
l = logging.getLogger("abg")
l.setLevel(logging.INFO)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
l.addHandler(ch)

## Surpresses annoying errors
pd.options.mode.chained_assignment = None
