import os
import sys
from configparser import ConfigParser

from datetime import datetime, timezone
try:
    from utility import calc_shift
except ModuleNotFoundError:
    from model.utility import calc_shift

APP_NAME = 'wsjtx-udp'

class Settings:
    
    def __init__(self):

        # compute data folder in user local storage
        p = os.getenv('LOCALAPPDATA')
        if p is None:
            s = sys.path[0]
            p = os.path.split(s)
            if p[1] == 'model':
                p = p[0]
            else:
                p = s
            self.df = os.path.join(p, 'data')
        else:
            self.df = os.path.join(l, APP_NAME)
        if not os.path.exists(self.df):
            os.makedirs(self.df)

        self.dbn = os.path.join(self.df, APP_NAME + '.sqlite')
        self.adifn = os.path.join(self.df, APP_NAME + '.adi')
        self.inin = os.path.join(self.df, APP_NAME + '.ini')

        if not os.path.exists(self.inin):
            self.defaults()
        else:
            self.config = ConfigParser()
            self.config.read(self.inin)

        self.platform = ''
        if os.name == 'nt':
            self.platform = 'win32'
        elif os.name == 'posix':
            if 'rpi' in os.uname().release:
                self.platform = 'rpi'
            else:
                self.platform = 'posix'
                
        
        self.park = ''
        self.shift = ''
        self.band = 0
        self.mode = None

    def defaults(self):
        self.config = ConfigParser()
        self.config['default'] = {
            'theme': 'clam',
            'wsjtx_host': '127.0.0.1',
            'wsjtx_port': '2237',
            'main_x': '20',
            'main_y': '20'
        }
        self.config['rpi'] = {
            'gps_host': '127.0.0.1',
            'gps_port': '2947'
        }
        self.config['win32'] = {
            'gps_port': 'COM5'
        }

    @property
    def wsjtx_address(self):
        return (self.config['default']['wsjtx_host'],
                int(self.config['default']['wsjtx_port']))

    @property
    def gps_address(self):
        if self.platform in ('rpi','posix'):
            return (self.config['rpi']['gps_host'],
                    int(self.config['rpi']['gps_port']))
        else:
            return self.config['win32']['gps_port']
            
    

    def update_status(self, d):
        self.band = d.dial_freq // 1_000_000
        n = datetime.now(timezone.utc)
        self.ordinal = n.toordinal()
        self.de_call = d.de_call.upper()
        self.grid = d.de_grid
        self.shift = calc_shift(self.grid, n.hour) if settings.park > '' else ''
        self.mode = d.mode

    def save(self):
        with open(self.inin, 'w') as f:
            self.config.write(f)
            
        
          
if __name__ == '__main__':
    settings = Settings()

