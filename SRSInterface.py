import numpy as np
import yaml
import time

from moxaSerial import Serial_TCPServer

class sim900_interface(Serial_TCPServer):
    
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        Serial_TCPServer.__init__(self, (self.ip, self.port))
        self.escape_string = 'xYzZyX'
        self.write('cons off')

    def escape(self):
        self.write(self.escape_string)

    def query(self,msg):
        self.write(msg)
        response = self.readline()    
        return response
    
    def identify(self):
        return self.query('*IDN?\r\n')

    def connect_to_sim_slot(self, sim_slot):
        self.escape()
        self.write('conn {0}, "{1}"'.format(sim_slot, self.escape_string))

    def write_to_sim_slot(self, sim_slot, message):
        self.connect_to_sim_slot(sim_slot)
        self.write(message)
        self.escape()
        
    def query_sim_slot(self, sim_slot, message):
        self.connect_to_sim_slot(sim_slot)
        response = self.query(message)
        self.escape()
        return response
        
class sim922_interface(sim900_interface):

    def __init__(self, ip, port, sim_slot):
        self.sim_slot = sim_slot
        self.ip = ip
        self.port = port
        sim900_interface.__init__(self, self.ip, self.port)

    def get_raw(self):
        return self.query_sim_slot(self.sim_slot, 'volt? 0')
    
    def get_ch_volt(self, ch):
        return self.query_sim_slot(self.sim_slot, 'volt? {0}'.format(ch))
    
    def get_raw_ch(self, ch):
        return self.query_sim_slot(self.sim_slot, 'volt? {0}'.format(ch))

    def set_ch_excitation(self, ch, state=1):
        self.write_to_sim_slot(self.sim_slot, 'exon {0}, {1}'.format(ch, state))
        
    def get_ch_excitation(self, ch):
        return self.query_sim_slot(self.sim_slot, 'exon? {0}'.format(ch))      
        
class sim921_interface(sim900_interface):

    def __init__(self, ip, port, sim_slot):
        self.sim_slot = sim_slot
        self.ip = ip
        self.port = port
        sim900_interface.__init__(self, self.ip, self.port)

    def set_freq(self, freq=40):
        self.write_to_sim_slot(self.sim_slot, 'freq {0}'.format(freq))

    def get_freq(self):
        return self.query_sim_slot(self.sim_slot, 'freq?')

    def set_range(self, r):
        self.write_to_sim_slot(self.sim_slot, 'rang {0}'.format(r))

    def get_range(self):
        return self.query_sim_slot(self.sim_slot, 'rang?')

    def set_exc_amp(self, exc):
        self.write_to_sim_slot(self.sim_slot, 'exci {0}'.format(exc))

    def get_exc_amp(self):
        return self.query_sim_slot(self.sim_slot, 'exci?')

    def exc_on(self):
        self.write_to_sim_slot(self.sim_slot, 'exon on')

    def exc_off(self):
        self.write_to_sim_slot(self.sim_slot, 'exon off')

    def set_exc_mode(self, mode = 2):
        self.write_to_sim_slot(self.sim_slot, 'mode {0}'.format(mode))

    def get_res(self):
        res = float(self.query_sim_slot(self.sim_slot, 'rval?'))
        return res

    def get_raw(self): # does same thing as get_res
        raw = self.query_sim_slot(self.sim_slot, 'rval?')
        return raw

    def autorange_gain(self, sleep=10):
        # takes about 10 seconds to recover after doing this, hence sleep
        self.write_to_sim_slot(self.sim_slot, 'agai 1')
        time.sleep(sleep)
        
class sim925_interface(sim900_interface):

    def __init__(self, ip, port, sim_slot):
        self.ip = ip
        self.port = port
        self.sim_slot = sim_slot
        sim900_interface.__init__(self, self.ip, self.port)

    def set_mux_chan(self, ch):
        self.write_to_sim_slot(self.sim_slot, 'chan {0}'.format(ch))


