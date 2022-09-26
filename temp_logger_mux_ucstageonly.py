import time
import os
import yaml
import sys

from SRSInterface import *

cal_dir = '/home/cubansandwich/inst_control/cal_files/'

####################
# load config file #
####################

config_file = '/home/cubansandwich/inst_control/config_hk_mux.yaml'
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

# make list of all thermometers
thermometer_names = []
for slot in slots:
    try:
        thermometer_names.append(config[slot]['Thermometer name'])
    except KeyError:
        pass
    for ch in range(1, 9):
        try:
            thermometer_names.append(config[slot][ch]['Thermometer name'])
        except KeyError:
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

    if module == 'SIM925':
        
        for ch in range(1, 9):
        
            try:
                cal_file = config[slot][ch]['Calibration file']
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

calibrator = {}
cal_temp = {}
cal_raw = {}
for cal_file in cal_files:
    cal_temp[cal_file], cal_raw[cal_file] = np.loadtxt(cal_dir + cal_file, skiprows=1, delimiter=',', unpack=True) 
    idx = np.argsort(cal_raw[cal_file])
    cal_temp[cal_file] = cal_temp[cal_file][idx]
    cal_raw[cal_file] = cal_raw[cal_file][idx]
    calibrator[cal_file] = lambda raw: np.interp(raw, cal_raw[cal_file], cal_temp[cal_file])

# find slots of 921 and 925
for slot in slots:
    try:
        if config[slot]['Module'] == 'SIM925':
            sim925_slot = slot
            sim921_slot = config[slot]['SIM921 slot']
    except KeyError:
        pass

# find mux channel for UC stage        
for ch in range(1, 9):
    try:
        if config[sim925_slot][ch]['Thermometer name'] == 'UC Stage':
            ucstage_ch = ch
    except KeyError:
        pass

# set mux to UC stage channel
muxer = sim925_interface(ip, port, sim925_slot)
muxer.set_mux_chan(ucstage_ch)
muxer.close()
time.sleep(.5)

# autocal sim921
print ('Autocal SIM921')
measurer = sim921_interface(ip, port, sim921_slot)
measurer.autorange_gain(sleep=60)
measurer.close()
  
# Do temperature logging
while True:
    
    loop_time = time.time()

    data_raw = {}
    data_cal = {}

    try:

        # Measure thermometers
        ######################

        for slot in slots:
    
            module = config[slot]['Module']
            
            # AC bridge measurement
            if module == 'SIM921':

                name = config[sim925_slot][ucstage_ch]['Thermometer name']
                cal_file = config[sim925_slot][ucstage_ch]['Calibration file']
                
                measurer = sim921_interface(ip, port, slot)
                
                x = []
                for k in range(11):
                    x.append(measurer.get_res())
                x = np.array(x)
                measurer.close()

                raw = np.median(x)
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

                    data_raw[name] = raw
                    data_cal[name] = cal
        
        for thermometer_name in thermometer_names:
            if thermometer_name not in list(data_raw):
                data_raw[thermometer_name] = np.nan
                data_cal[thermometer_name] = np.nan
                
        # Print calibrated values to terminal
        #####################################

        for key in sorted(data_cal.keys()):
            print key + format(data_cal[key], '.3f').rjust(20-len(key))
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
        #with open(save_file_cal, 'a') as f:
        #    f.write(str(loop_time))
        #    for key in sorted(data_cal.keys()):
        #        f.write(',' + str(data_cal[key]))
        #    f.write('\n')
            
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

    except KeyboardInterrupt as e:

        try:
            measurer.escape()
            measurer.close()
            muxer.close()
        except:
            pass
            
        break
