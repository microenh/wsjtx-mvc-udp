from os import path
from configparser import ConfigParser

class Settings:
    def __init__(self, inin):
        self.inin = inin
        # print(self.inin)
        if not path.exists(self.inin):
            self.defaults()
        else:
            self.config = ConfigParser()
            self.config.read(self.inin)

    def defaults(self):
        self.config = ConfigParser()
        self.config['default'] = {
            'theme': 'clam',
            'wsjtx_host': '127.0.0.1',
            'wsjtx_port': '2237',
            'main_x': '20',
            'main_y': '20',
            'park': '',
            'shift': ''
        }
        self.config['rpi'] = {
            'gps_host': '127.0.0.1',
            'gps_port': '2947'
        }
        self.config['win32'] = {
            'gps_port': 'COM4'
        }

    def save(self):
        with open(self.inin, 'w') as f:
            self.config.write(f)
               
          
if __name__ == '__main__':
    settings = Settings()
