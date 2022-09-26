import numpy as np
import time
import os
import pickle as pkl
import yaml
import datetime

import pydfmux
from pydfmux.algorithms.bolo.zero_combs import zero_combs
from pydfmux.core.utils.conv_functs import build_hwm_query
from pydfmux.core.utils.dfmux_logging import LoggingManager
from pydfmux.algorithms.squid.offset_zero import offset_zero
LM = LoggingManager()

###############
# load config #
###############

hwm_file = '/home/cubansandwich/hardware_maps/lbnl/black_dewar/hwm.yaml'

############
# load HWM #
############

with open(hwm_file, 'r') as f:
    s = pydfmux.load_session(f)
    hwm = s['hardware_map']
ds = hwm.query(pydfmux.Dfmux)
ds.resolve()
d = ds[0]

######################
# define HWM queries #
######################

squids = hwm.query(pydfmux.SQUID)
sqmods = hwm.query(pydfmux.SQUIDModule)
rmods = hwm.query(pydfmux.ReadoutModule)
sqcbs = hwm.query(pydfmux.SQUIDController)
iceboard = hwm.query(pydfmux.IceBoard)
mezz = hwm.query(pydfmux.MGMEZZ04)
bolos = hwm.query(pydfmux.Bolometer)
bolos_obed = bolos.filter(pydfmux.Bolometer.state=='overbiased')
bolos_ob = bolos.filter(pydfmux.Bolometer.overbias=='True')

#############
# functions #
#############

def offset_zero_sqmods(sqmods)
    for sqmod in sqmods:
        offset_zero(sqmod)        
