import yaml

#from Communicable import Communicable
from moxaSerial_modified import Serial_TCPServer
#from moxaSerial import Serial_TCPServer

#################
#################
'''
class ps_interface_usb(Communicable):

    def __init__(self, port):
        self.port = port
        Communicable.__init__(self, self.port)
        self.write('SYST:REM') # sets to remote mode

    ####################
    # helper functions #
    ####################
    
    def identify(self):
        return self.query('*IDN?')
        
    def select_ch(self, ch):
        self.write('INST:NSEL {0}'.format(ch))

    ##############
    # set things #
    ##############
    
    def set_ch_volt(self, ch, volt):
        self.select_ch(ch)
        self.write('VOLT {0}'.format(volt))
        
    def set_ch_curr(self, ch, curr):
        self.select_ch(ch)
        self.write('CURR {0}'.format(curr))
               
    def channel_on(self, ch):
        self.select_ch(ch)
        self.write('CHAN:OUTP 1')
        
    def channel_off(self, ch):
        self.select_ch(ch)
        self.write('CHAN:OUTP 0')
    
    ###########
    # queries #
    ###########

    def get_ch_volt_lim(self, ch):
        self.select_ch(ch)
        volt = self.query('VOLT?')
        return volt   
        
    def get_ch_curr_lim(self, ch):
        self.select_ch(ch)
        curr = self.query('CURR?')
        return curr
        
    def get_ch_volt(self, ch):
        volt = self.query('MEAS? CH{0}'.format(ch))
        return volt
        '''
#################
#################

class ps_interface_moxa(Serial_TCPServer):

    def __init__(self, ip, port):
        
        # set attributes
        self.ip = ip
        self.port = port

        # inherit moxa communication
        Serial_TCPServer.__init__(self, (self.ip, self.port))
    
        # set power supply into remote mode
        self.set_remote()
           
    ####################
    # helper functions #
    ####################
    
    def set_remote(self):
        self.connect()
        self.write('SYST:REM')
        self.close()
                
    def identify(self):
        self.connect()
        idn = self.query('*IDN?')
        self.close()
        return idn

    ##############
    # set things #
    ##############
    
    def set_ch_volt(self, ch, volt):
        self.connect()
        self.write('INST:NSEL {0}'.format(ch))
        self.write('VOLT {0}'.format(volt))
        self.close()
        
    def set_ch_curr(self, ch, curr):
        self.connect()
        self.write('INST:NSEL {0}'.format(ch))
        self.write('CURR {0}'.format(curr))
        self.close()
               
    def channel_on(self, ch):
        self.connect()
        self.write('INST:NSEL {0}'.format(ch))
        self.write('CHAN:OUTP 1')
        self.close()
                
    def channel_off(self, ch):
        self.connect()
        self.write('INST:NSEL {0}'.format(ch))
        self.write('CHAN:OUTP 0')
        self.close()
            
    ###########
    # queries #
    ###########

    def get_ch_volt_lim(self, ch):
        self.connect()
        self.write('INST:NSEL {0}'.format(ch))
        volt = self.query('VOLT?')
        self.close()
        return volt   
        
    def get_ch_curr_lim(self, ch):
        self.connect()
        self.write('INST:NSEL {0}'.format(ch))
        curr = self.query('CURR?')
        self.close()
        return curr
        
    def get_ch_volt(self, ch):
        self.connect()
        volt = self.query('MEAS? CH{0}'.format(ch))
        self.close()
        return volt
