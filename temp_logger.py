import time
import os
import yaml
import sys

from SRSInterface import *

cal_dir = '/home/cubansandwich/inst_control/cal_files/'

####################
# load config file #
####################

config_file = '/home/cubansandwich/inst_control/config_hk.yaml'
with open(config_file, 'r') as f:
    config = yaml.safe_load(f)

save_file_cal = config['Temperature log']
save_file_raw = save_file_cal[:-4] + '_raw.txt'

###################
# Load SRS config #
###################

with open(config_file, 'r') as f:
    config = yaml.safe_load(f)['SRS Mainframe']

# Instantiate SRSInterface objects
ip = config['moxa']['ip']
port = config['moxa']['port']

# find slots that have things in them
slots = []
for k in range(1, 9):
    try:
        module = config[k]['Module']
        slots.append(k)
    except:
        pass

# Make calibrator functions
cal_files = []

for slot in slots:
    
    try:
        module = config[slot]['Module']
    except:
        continue

    if module == 'SIM921':
        
        try:
            cal_file = config[slot]['Calibration file']
        except:
            continue
        
        if cal_file not in cal_files:
            cal_files.append(cal_file)

    if module == 'SIM922':

        for ch in range(1, 5):
            
            try:
                cal_file = config[slot][ch]['Calibration file']
            except:
                continue

            if cal_file not in cal_files:
                cal_files.append(cal_file)

# define autorange function
def autorange_resistance(resistance):
    if resistance < 1e-2:
        return 0
    elif resistance >= 1e-2 and resistance < 1e-1:
        return 1
    elif resistance >= 1e-1 and resistance < 1e0:
        return 2
    elif resistance >= 1e0 and resistance < 1e1:
        return 3
    elif resistance >= 1e1 and resistance < 1e2:
        return 4
    elif resistance >= 1e2 and resistance < 1e3:
        return 5
    elif resistance >= 1e3 and resistance < 1e4:
        return 6
    elif resistance >= 1e4 and resistance < 1e5:
        return 7
    elif resistance >= 1e5 and resistance < 1e6:
        return 8
    elif resistance >= 1e6:
        return 9

######        
calibrator = {}
cal_temp = {}
cal_raw = {}
for cal_file in cal_files:
    cal_temp[cal_file], cal_raw[cal_file] = np.loadtxt(cal_dir + cal_file, skiprows=1, delimiter=',', unpack=True) 
    idx = np.argsort(cal_raw[cal_file])
    cal_temp[cal_file] = cal_temp[cal_file][idx]
    cal_raw[cal_file] = cal_raw[cal_file][idx]
    calibrator[cal_file] = lambda raw: np.interp(raw, cal_raw[cal_file], cal_temp[cal_file])

# autorange gains on sim921s
'''print 'autoranging, wait 60 seconds'
for slot in slots:

    module = config[slot]['Module']

    if module == 'SIM921':
        measurer = sim921_interface(ip, port, slot)                
        measurer.autorange_gain(sleep=1)
        measurer.close()
time.sleep(60)'''

# Do temperature logging
FIRST_ITERATION=True
while True:
    
    time.sleep(2)
    
    loop_time = time.time()

    data_raw = {}
    data_cal = {}
    ran = {}
    if FIRST_ITERATION: 
        ran_prev={}    
    try:

        # Measure all thermometers
        ##########################

        for slot in slots:
    
            module = config[slot]['Module']
            
            # AC bridge measurement
            if module == 'SIM921':
                    
                name = config[slot]['Thermometer name']
                cal_file = config[slot]['Calibration file']
                            
                measurer = sim921_interface(ip, port, slot) 

                if FIRST_ITERATION:
                    ran[name] = 9
                    measurer.set_range(ran[name])

                else:
                    ran[name] = autorange_resistance(data_raw_prev[name])
                    if ran[name]!=ran_prev[name]:
                        measurer.set_range(ran[name])
                    
                raw = measurer.get_raw()
                measurer.close()
                
                cal = calibrator[cal_file](raw)

                data_raw[name] = raw
                data_cal[name] = cal

            # Diode monitor measurement
            if module == 'SIM922':
                     
                for ch in range(1, 5):
                    
                    measurer = sim922_interface(ip, port, slot)
                    raw = float(measurer.get_ch_volt(ch))
                    measurer.close()

                    name = config[slot][ch]['Thermometer name']
                    cal_file = config[slot][ch]['Calibration file']

                    cal = calibrator[cal_file](raw)

                    data_raw[name] = raw#[ch-1]
                    data_cal[name] = cal
        
        # Print calibrated values to terminal
        #####################################

        for key in sorted(data_cal.keys()):
            s1 = key
            s2 = format(data_cal[key], '.3f').rjust(20-len(s1))
            s3 = format(data_raw[key], '.3f').rjust(20-len(s2))
            print s1+s2+s3
            #print key + format(data_cal[key], '.3f').rjust(20-len(key)) + format(data_raw[key], '.3f').rjust(20-len(key))
        print ''

        # Save calibrate data to save_cal_file
        ######################################

        # If save_file_cal does not exist, make it
        # and write the header
        try:
            with open(save_file_cal, 'r') as f:
                pass
        except IOError: 
            with open(save_file_cal, 'w') as f:
                f.write('Time')
                for key in sorted(data_cal.keys()):
                    f.write(',' + str(key))
                f.write('\n')
                
        # Append data_cal to save_file_cal
        write_str = str(loop_time)
        for key in sorted(data_cal.keys()):
            write_str += ',' + str(data_cal[key])
        write_str += '\n'
        with open(save_file_cal, 'a') as f:
            f.write(write_str)
            
        # Save raw data to save_file_raw
        ################################

        # If save_file_raw does not exist, make it
        # and write the header
        try:
            with open(save_file_raw, 'r') as f:
                pass
        except IOError:
            with open(save_file_raw, 'w') as f:
                f.write('Time')
                for key in sorted(data_cal.keys()):
                    f.write(',' + str(key))

        # Append data_raw to save_file_raw
        with open(save_file_raw, 'a') as f:
            f.write('\n' + str(loop_time))
            for key in sorted(data_raw.keys()):
                f.write(',' + str(data_raw[key]))

        # cache data_raw and ran for autorange on next iteration
        ################################################
        data_raw_prev = data_raw.copy()
        ran_prev = ran.copy()
        
        FIRST_ITERATION = False
        
    except KeyboardInterrupt as e:

        try:
            measurer.escape()
            measurer.close()
        except:
            pass
            
        break
