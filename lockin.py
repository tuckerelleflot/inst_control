import Gpib 

import numpy as np
import time
import os
import pickle as pkl
import yaml
import glob

import pydfmux
from pydfmux.algorithms.bolo.zero_combs import zero_combs
from pydfmux.core.utils.conv_functs import build_hwm_query

############
# load HWM #
############

hwm_file = '/home/cubansandwich/hardware_maps/lbnl/black_dewar/hwm_testing.yaml'

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
sqcbs = hwm.query(pydfmux.SQUIDController)

############################
# define pydfmux functions #
############################

def bootup(fir_stage=6):
    for board in hwm.query(pydfmux.IceBoard):
       board.clear_all()
    ds.initialize_iceboard()
    ds.set_fir_stage(fir_stage)
    for d in ds:
        d.set_timestamp_port(d.TIMESTAMP_PORT.TEST)
    for sqcb in sqcbs:
        try:
            sqcb.initialize_squidcontroller()
        except:
            print('Initialization failed for at least one SQUID controller - you should do something about this if you care.')
            
def set_gains(gain, target_dac = ['NULLER','CARRIER'], boards = ds):
    if type(target_dac) == 'str':
        target_dac = [target_dac]

    for dac in target_dac:
        for i in range(1,3):
            for j in range(1,5):
              for board in boards:
                try:
                  board.set_mezzanine_gain(gain = gain, target = dac, module = j, mezzanine = i)
                except:
                  print 'failed to set gain on', board, ', mezzanine ', i


def turn_on_nuller_tone(squid, freq, amp, phase=0):
    chan = squid.module.readout_module.channel[59]
    chan.set_frequency(freq, d.UNITS.HZ, d.TARGET.NULLER)
    chan.set_amplitude(amp, d.UNITS.NORMALIZED, d.TARGET.NULLER)
    chan.set_phase(phase, d.UNITS.DEGREES, d.TARGET.NULLER)
    
############################
# define lock-in functions #    
############################

inst = Gpib.Gpib(0, 8)

def get_freq():
    inst.write('freq?')
    time.sleep(0.5)
    freq = inst.read().strip()
    return freq
    
def set_signal_input_impedance(fiftyohm=True):
    if fiftyohm:
        inst.write('inpz 0')
    if not fiftyohm:
        inst.write('inpz 1')
        
def auto_sensitivity():
    inst.write('agan')
    
def snap(n=10):
    #x = np.empty((n, 4))
    x = []
    for k in range(10):
        inst.write('snap?1,2,5,8')
        time.sleep(1)
        out = np.array(inst.read().strip().split(','), dtype=float)
        x.append(out)
    x = np.array(x)
    return x

def clear_buffer():
    for k in range(10):
        try:
            inst.read()
        except:
            break

##################    
# do measurement #
##################
            
def do_measurement(freqs, signal_amps, reference_amps, gain=0, npts=10, save=True):
    
    zero_combs(ds)
    set_gains(gain)
    
    x = []
    
    for freq in freqs:
        
        print('\n' + 'Measuring at ' + str(round(freq)) + ' Hz')
            
        for reference_amp in reference_amps:
            for signal_amp in signal_amps:
              
                # turn on reference tone and signal tone and let settle
                print('\n\t' + 'setting tone amplitudes')
                turn_on_nuller_tone(squids[4], freq, reference_amp)
                turn_on_nuller_tone(squids[0], freq, signal_amp)
                time.sleep(3)
        
                # get lock-in reading
                print('\t' + 'reading values from lock in')
                for k in range(npts):
                    inst.write('snap?1,2,3,5,8')
                    out = inst.read().strip().split(',')
                    x.append([time.time(), freq, reference_amp, signal_amp, out[0], out[1], out[2], out[3], out[4]])
                    time.sleep(1)
                    
                # turn off reference tone and signal tone and let settle
                #print('\n\t' + 'zeroing tone amplitudes')
                #turn_on_nuller_tone(squids[4], freq, 0)
                #turn_on_nuller_tone(squids[0], freq, 0)
                #time.sleep(3)                    

    x = np.array(x)
    x = x.astype(float)

    # save
    if save:
        save_dir = '/home/cubansandwich/nuller_TF_lockin/'
        fnames = sorted(glob.glob(save_dir + '*'))
        for k in range(100):
            if not any(str(k).zfill(3) in fname for fname in fnames):
                save_file = save_dir + str(k).zfill(3) + '.txt'
                break

        with open(save_file, 'w') as f:
            f.write('time, command frequency [Hz], referece amp [DAC], signal amp [DAC], x [V], y [V], R [V], phase [deg], demod frequency [Hz]')
        
            for j in range(len(x)):
                f.write('\n' + str(x[j][0]))
                for k in range(1, len(x[0])):
                    f.write(', ' + str(x[j][k]))
                    
    return x       








