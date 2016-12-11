
import logging

logging.basicConfig(filename='/tmp/abg.log')
l = logging.getLogger("abg")
l.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
l.addHandler(ch)
