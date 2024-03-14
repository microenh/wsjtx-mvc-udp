from library.serial_base import SerialBase
from library.utility import grid_square, timefromgps, todec, settimefromgps

from library.event import NotifyGUI
from library.settings import settings
from library.tx_msg import location

class GPS(SerialBase):
    def __init__(self):
        super().__init__(settings.gps_port, 9600)
        self.message = ''
        self.grid = None
        self.update_time_request = False

    def update_time(self):
        self.update_time_request = True

    def update_grid(self, grid, wsjtx):
        if grid is not None:
            wsjtx.send(location(grid))
            self.message = f'grid set to {grid}'
        
    def report(self, is_open):
        self.push(NotifyGUI.GPS_OPEN if is_open else NotifyGUI.GPS_CLOSE)        

    def process(self, data):
        a = data.decode().strip().split(',')
        match a[0]:
            case '$GPRMC':
                _, utc, _, la, la_dir, lo, lo_dir, _, _, dt = a[:10]
                tm = timefromgps(utc)
                lat = todec(la, la_dir)
                lon = todec(lo, lo_dir)
                grid = grid_square(lon,lat)
                if grid is not None:
                    grid = grid[:6]
                if self.update_time_request:
                    self.update_time_request = False
                    self.message = settimefromgps(dt, tm)
                if self.message > '':
                    self.push(NotifyGUI.GPS_MSG, self.message)
                    self.message = ''
                else:
                    self.push(NotifyGUI.GPS_DATA, {'time': tm, 'grid': grid}) 

if __name__ == '__main__':
    from main import main
    main()

"""
from gpsdclient import GPSDClient
# or as python dicts (optionally convert time information to `datetime` objects)
with GPSDClient() as client:
    for result in client.dict_stream(convert_datetime=True, filter=["TPV"]):
        print("Latitude: %s" % result.get("lat", "n/a"))
        print("Longitude: %s" % result.get("lon", "n/a"))
"""
