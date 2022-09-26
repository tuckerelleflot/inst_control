import yaml
from subprocess import check_output
import numpy as np
import time
import sys

from PowerSupplyInterface import *

class thermometer():

    def __init__(self, temp_log, temp_log_name):

        self.temp_log = temp_log
        self.temp_log_name = temp_log_name
        
        self.configure_temperature_info()

    def configure_temperature_info(self):
        names = check_output('head -n1 ' + str(self.temp_log), shell=True)
        names = names.split('\n')[0]
        names = names.split(',')

        if self.temp_log_name not in names:
            print 'Check that temp_log_name matches the name in the temp log file'
            print self.temp_log
            print self.temp_log_name
            return
            
        for idx, name in enumerate(names):
            if name == self.temp_log_name:
                break
        self.idx = idx 

    def get_temp(self):
        x = check_output('tail -1 ' + str(self.temp_log), shell=True)
        x = x.split('\n')
        x = x[0].split(',')
        temp = float(x[self.idx])
        return temp

class heater(ps_interface_moxa, thermometer):
 
    def __init__(self, moxa_ip=False, moxa_port=False, ch=False, temp_log=False, temp_log_name=False, kp=0, ki=0, v_max=0):
        
        # set up attributes
        self.moxa_ip = moxa_ip
        self.moxa_port = moxa_port
        self.ch = ch
        self.temp_log = temp_log
        self.temp_log_name = temp_log_name
        self.kp = kp
        self.ki = ki
        self.v_max = v_max

        # inherit ps_interface_moxa class
        ps_interface_moxa.__init__(self, self.moxa_ip, self.moxa_port)
        
        # inherit thermometer class
        thermometer.__init__(self, self.temp_log, self.temp_log_name)
                
    def set_volt(self, volt):
        self.set_ch_volt(self.ch, volt)
        
    def set_curr(self, curr):
        self.set_ch_curr(self.ch, curr)
        
    def get_volt(self):
        volt = self.get_ch_volt(self.ch)
        return volt
    
    def on(self):
        self.channel_on(self.ch)
        
    def off(self):
        self.channel_off(self.ch)
        
    def proportional(self, set_point):
        temp = self.get_temp()
        err = set_point - temp
        v = err*self.kp
        return v

    def integral(self, set_point, accumulated_err):
        v = accumulated_err*self.ki
        return v
        
    def set_temp(self, set_point, accumulated_err=0):
        vp = self.proportional(set_point)
        #vi = self.integral(set_point, accumulated_err)
        vi = 0
        v = vp + vi
        if v > self.v_max:
            v = self.v_max
        if v<0:
            v = 0
        self.set_volt(v)
