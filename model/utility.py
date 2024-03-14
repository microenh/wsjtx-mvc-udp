from sys import platform
from datetime import date, datetime, timezone

if platform == 'linux':
    import time


if platform == 'win32':
    from win32api import SetSystemTime

def timestamp():
    return datetime.now(timezone.utc).strftime('%M:%S')

DIVISIONS = (
    ( 1, ord('A')),
    (10, ord('0')),
    (24, ord('a')),
    (10, ord('0')), 
    (24, ord('A'))
)
    
def grid_square(lon, lat):
    """
    lon: decimal longitude -180 .. 180 (West is negative)
    lat: decimal latitude -90 .. 90 (South is negative)
    returns 10 character string 'AA99aa99AA' (truncate for less precision)
    """
    if lat is not None and lon is not None:
        lat += 90
        lon += 180
        lon_div = 20.0
        lat_div = 10.0

        results = []
        for div, base in DIVISIONS:
            lon_div /= div
            lat_div /= div
            results.append(chr((lo := int(lon / lon_div)) + base)
                         + chr((la := int(lat / lat_div)) + base))
            lon -= lo * lon_div
            lat -= la * lat_div
            
        return ''.join(results)

def lon_lat(grid_square):
    """
    grid_square: AA99aa99AA or any 2,4,6,8 character subset
    """
    lon = -180.0
    lat = -90.0
    lon_mult = 20.00
    lat_mult = 10.0
    for m,p in DIVISIONS:
        if len(grid_square)< 2:
            break        
        lon_mult /= m
        lat_mult /= m
        lon += lon_mult * (ord(grid_square[0]) - p)
        lat += lat_mult * (ord(grid_square[1]) - p)
        grid_square = grid_square[2:]
    return lon, lat

def timefromgps(utctime):
    if utctime > '':
        h = int(utctime[:2])
        m = int(utctime[2:4])
        s = int(utctime[4:6])
        return (h,m,s)

def todec(x,h):
    if x > '':
        r = float(x[:(a:=-8)]) + (float(x[a:]) / 60.0)
        return r if h in 'NE' else -r

def calc_shift(gs, h):
    """
    'e': early shift
    'l': late shift
    'r': regular shift
    gs: grid_sqaure at least 'AA99'
    h: hour after midnight UTC
    """
    a = calc_shift  # reference function 'static' variables
    try:
        if gs == a.gs and h == a.h:
            return a.s
    except AttributeError:
        pass
    a.h = h
    a.gs = gs
    lon, _ = lon_lat(gs)
    adj = int(round(lon / 15))
    h = (h + adj - 2) % 24
    if h < 6:
        a.s = 'e'
    elif h < 16:
        a.s = 'r'
    else:
        a.s = 'l'
    # print(a.s)
    return a.s



def settimefromgps(day, t):
    if day > '' and time is not None:
        """
        day: ddmmyy
        time: hhmmss.ss
        """
        d = int(day[:2])
        mon = int(day[2:4])
        y = int(day[4:]) + 2000
        h,m,s = t
        # print(y, mon, dt.weekday(), d, h, m, s, 0)
        if platform == 'win32':
            dt = date(y,mon,d)
            try:
                SetSystemTime(y, mon, dt.weekday(), d, h, m, s, 0)
                return 'Time set'
            except Exception as e:
                return e.strerror
        if platform == 'linux':
            try:
                dt = datetime(y, mon, d, h, m, s)
                time.clock_settime(time.CLOCK_REALTIME, dt.timestamp())
                return 'Time set'
            except Exception as e:
                return e.strerror


if __name__ == '__main__':
##    for i in (
##        ('PM85kh', 'rrrrrrrrrlllllllleeeeeer'),  # Japan
##        ('DM07kp', 'rrlllllllleeeeeerrrrrrrr'),  # California     
##        ('EM89hu', 'lllllllleeeeeerrrrrrrrrr'),  # Ohio
##        ('IO91wm', 'lleeeeeerrrrrrrrrrllllll'),  # UK -longitude
##        ('JO01ir', 'lleeeeeerrrrrrrrrrllllll'),  # UK +longitude
##        ('KO01hr', 'leeeeeerrrrrrrrrrlllllll'),  
##        ('KO21pu', 'eeeeeerrrrrrrrrrllllllll'),
##        ('KN89vw', 'eeeeerrrrrrrrrrlllllllle'),  # Ukraine UR-0025
##    ):
##        r = ''.join([calc_shift(i[0], hr) for hr in range(24)])
##        print(i[0], r==i[1])
    settimefromgps(0)
