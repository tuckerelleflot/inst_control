import yaml
from subprocess import check_output
import numpy as np
import time
import sys
from datetime import datetime

from PowerSupplyInterface import *
from FridgeInterface import *


def PID(x, condition='True', verbose=True):

    # x is a list of objects and set point temperatures, i.e.
    # x = [[ucpu, 40], [icpu, 40], [he4pu, 40]]
    
    # condition is a conditional statement. as long as condition evaluates to True, then the PID loop will continue
    # examples of conditions:
    # condition = 'ucpu.get_temp()<40'    (keeps PID going until temperature of ucpu is no longer less than 40)
    
    width = 20
    
    if verbose:
        sys.stdout.write('\nPID -- Condition: ' + condition + '\n\n')
        sys.stdout.write('OBJECT'.ljust(width, ' ') + 'TEMPERATURE'.ljust(width, ' ') + 'SET POINT'.ljust(width, ' ') + 'VOLTAGE\n')
    
    for k in range(len(x)):
        x[k].append(0) # this is the acculumated error entry, 0 so far

    while True:
        if eval(condition):
            for k in range(len(x)):
                time.sleep(.2)
                
                ob = x[k][0] # object
                sp = x[k][1] # set point

                v_max = ob.v_max
                    
                pv = ob.get_temp() # temperature
                err = sp - pv
                x[k][2] += err
                acc_err = x[k][2] # accumulated error
               
                vp = ob.proportional(sp)
                vi = ob.integral(sp, acc_err)
                v = vi + vp
                if v > v_max:
                    v = v_max
                if v < 0:
                    v = 0
                ob.set_volt(v) 

                v = str(round(float(ob.get_volt()), 2))

                if verbose:
                    sys.stdout.write(ob.temp_log_name.ljust(width, ' ') + str(round(pv,3)).ljust(width, ' ') + str(sp).ljust(width, ' ')+ v + '\n')
            
            if verbose:
                sys.stdout.flush()
                for k in range(len(x)):
                    sys.stdout.write('\033[F')
    
            time.sleep(1)
        else:
            break
            
def all_on():
    ucpu.on()
    icpu.on()
    he4pu.on()
    ucsw.on()
    icsw.on()
    he4sw.on()

def cycle_fridge(preheated=False):
    
    print datetime.now().strftime('%H:%M:%S') + ' UTC -- STARTING FRIDGE CYCLE'
    
    if not preheated:
        # turn off pump heaters
        print datetime.now().strftime('%H:%M:%S') + ' UTC -- TURNING OFF PUMP HEATERS'
        ucpu.set_volt(0)
        icpu.set_volt(0)
        he4pu.set_volt(0)
    
        # cool switches 
        print datetime.now().strftime('%H:%M:%S') + ' UTC -- COOLING SWITCHES'
        ucsw.set_volt(0)
        icsw.set_volt(0)
        he4sw.set_volt(0)
        while True:
            if ucsw.get_temp() < 7 and icsw.get_temp() < 7 and he4sw.get_temp() < 7:
                break
            else:
                time.sleep(10)
        
        # heat pumps 
        print datetime.now().strftime('%H:%M:%S') + ' UTC -- HEATING PUMPS'
        run_time_sec = 1*60*60 # one hours
        for k in range(run_time_sec):
            try:
                ucpu.set_temp(35)
                icpu.set_temp(35)
                he4pu.set_temp(40)
                time.sleep(1)
            except IndexError:
                print('Index error')
                time.sleep(1)
    
    # turn off pump heaters and let mainplate cool off a bit
    print datetime.now().strftime('%H:%M:%S') + ' UTC -- LETTING MAINPLATE COOL'
    he4pu.set_volt(0)
    ucpu.set_volt(0)
    icpu.set_volt(0)
    run_time_sec = 20*60 # 20 minutes
    for k in range(run_time_sec):
        try:
            if ucpu.get_temp() < 30.1:
                break
            if icpu.get_temp() < 30.1:
                break
            else:
                time.sleep(1)
        except IndexError:
            print('Index error')
            time.sleep(1)
    
    # heat he4 switch, uc pump, ic pump
    print datetime.now().strftime('%H:%M:%S') + ' UTC -- COOLING HE4 PUMP'
    while True:
        try:
            if exch.get_temp()<1.8:
                break
            else:
                ucpu.set_temp(30)
                icpu.set_temp(30)
                he4sw.set_temp(18)
                time.sleep(1)
        except IndexError:
            print('Index error')
            time.sleep(1)
    
    run_time_sec = 20*60 
    for k in range(run_time_sec):
        try:
            ucpu.set_temp(40)
            icpu.set_temp(40)
            he4sw.set_temp(18)
            time.sleep(1)
        except IndexError:
            print('Index error')
            time.sleep(1)
    
    while True:
        try:
            if exch.get_temp()>2.:
                break
            else:
                ucpu.set_temp(40)
                icpu.set_temp(40)
                he4sw.set_temp(18)
                time.sleep(1)
        except IndexError:
            print('Index error')
            time.sleep(1)

    # cool IC head and UC head
    print datetime.now().strftime('%H:%M:%S') + ' UTC -- COOLING IC PUMP'
    icpu.set_volt(0)
    ucpu.set_volt(0)
    run_time_sec = 30*60
    for k in range(run_time_sec):
        try:
            icsw.set_temp(18)
            he4sw.set_temp(18)
            time.sleep(1)
        except IndexError:
            time.sleep(1)
    run_time_sec = 20*60
    print datetime.now().strftime('%H:%M:%S') + ' UTC -- COOLING UC PUMP'
    for k in range(run_time_sec):
        try:
            icsw.set_temp(18)
            he4sw.set_temp(18)
            ucsw.set_temp(18)
            time.sleep(1)
        except IndexError:
            time.sleep(1)

def set_ucstage_temp(sp=0.7, kp=100., ucpu_v_max=20.):

    # Use this to set the UC head temperature
    #
    # When increasing temperature, it's ok to do it in one big step
    #
    # When decreasing temperature, it works best to use several small steps (dTemp of 50-100 mK)
    # instead of one big step
    #
    # Note:
    #       sp = 0.80 heats UC stage to ~ 570 mK
    #       sp = 0.50 heats UC head to ~390 mK
    #       sp = 0.00 will drop UC head to base temperature

    dt = 1
    
    while True:
    
        ############################
        # PID all switches to 19 K #
        ############################

        ucsw.set_temp(19)
        icsw.set_temp(19)
        he4sw.set_temp(19)
        
        #######################
        # PID IC pump to 20 K #
        #######################
        
        if sp !=0:

            v = icpu.proportional(20)

            if v > icpu.v_max:
                v = icpu.v_max
            if v < 0:
                v = 0

            icpu.set_volt(v) 
        
        if sp == 0:
        
            icpu.set_volt(0)

        #########################################
        # Heat UC head using UC pump as control #
        #########################################
        
        pv = ucstage.get_temp()
        
        # calculate proportional term
        err = sp - pv
        vp = err * kp
        
        # calculate integral term
        vi = 0 # not using integral now
        
        # get total voltage
        v = vp + vi
        
        # prevent UC pump from getting above Thi (Thi should be ~20 K)
        n = 20
        Thi = 20
        v = v * (1 - (ucpu.get_temp() / Thi) ** n )
        
        # check that voltage is reasonable
        if v > ucpu_v_max:
            v = ucpu_v_max
        if v < 0.:
            v = 0.
        
        # set UC pump voltage
        ucpu.set_volt(v)
        
        print v
        print ''
        
        # wait
        time.sleep(dt)       

def heat_pumps_during_cooldown():
    
    icsw.set_volt(0)
    ucsw.set_volt(0)
    he4sw.set_volt(0)
    
    while True:
        
        # factor to account for switch temperatures
        if ucsw.get_temp()>10 or icsw.get_temp()>10 or ucsw.get_temp()>10:
            factor = 0
        else:
            factor = 1
            factor = factor * (1 - (ucsw.get_temp() / 10) ** 17 )
            factor = factor * (1 - (icsw.get_temp() / 10) ** 17 )
            factor = factor * (1 - (he4sw.get_temp() / 10) ** 17 )
        
        # set He4 pump voltage
        v = he4pu.proportional(70)
        if v < 0:
            v = 0
        else:
            v = v * factor
            if v < 0:
                v = 0
            elif v > he4pu.v_max:
                v = he4pu.v_max
        he4pu.set_volt(v)
        print ('He4 pump: ' + str(round(v, 1)))
        
        # set IC pump voltage
        v = icpu.proportional(70)
        if v < 0:
            v = 0
        else:
            v = v * factor
            if v < 0:
                v = 0
            elif v > icpu.v_max:
                v = icpu.v_max
        icpu.set_volt(v)
        print ('IC pump: ' + str(round(v, 1)))
        
        # set UC pump voltage
        v = ucpu.proportional(70)
        if v < 0:
            v = 0
        else:
            v = v * factor
            if v < 0:
                v = 0
            elif v > ucpu.v_max:
                v = ucpu.v_max                  
        ucpu.set_volt(v)
        print('UC pump: ' + str(round(v, 1)))
        
        print('')
        
        time.sleep(1)

###################################################################
###################################################################
        
if __name__ == '__main__':

    config_file = '/home/cubansandwich/inst_control/config_hk_mux.yaml'
    
    try:
    
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        # get temp_log 
        temp_log = config['Temperature log']

        # make heater objects            
        for ps in config['Power supplies'].keys():

            moxa_ip = config['Power supplies'][ps]['moxa']['ip']
            moxa_port = config['Power supplies'][ps]['moxa']['port']

            for out in config['Power supplies'][ps].keys():                
                            
                if 'out' in out:
                    ch = out[-1]
                    for setting in config['Power supplies'][ps][out].keys():
                        vars()[setting] = config['Power supplies'][ps][out][setting]
                    vars()[short_name] = heater(moxa_ip, moxa_port, ch, temp_log=temp_log, temp_log_name=long_name, kp=kp, v_max=v_max)
        
        # make thermometer objects
        uchead = thermometer(temp_log, 'UC Head')
        ichead = thermometer(temp_log, 'IC Head')
        ucstage = thermometer(temp_log, 'UC Stage')
        exch = thermometer(temp_log, 'Exchanger')            

    except Exception as e:
        print e
        pass
