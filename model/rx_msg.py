from struct import unpack_from, calcsize
from datetime import datetime, timedelta, timezone

def to_datetime(jday, msec, timespec, offset):
    dt = (datetime.fromordinal(jday - 1721425) + timedelta(seconds=msec/1000))
    match timespec:
        case 0:
            dt = dt.astimezone()
        case 1|2:
            dt = dt.replace(tzinfo=timezone(timedelta(seconds=offset)))    
    return dt

def parse(d):

    def parse_base(a, fmt):
        a._index = (o:=a._index) + calcsize(fmt)
        return unpack_from(fmt, a.raw, o)[0]

    qbool = lambda a: parse_base(a, '?')
    qint8 = lambda a: parse_base(a, 'b')
    quint8 = lambda a: parse_base(a, 'B')
    quint16 = lambda a: parse_base(a, '>H')
    qint32 = lambda a: parse_base(a, '>i')
    quint32 = lambda a: parse_base(a, '>I')
    qint64 = lambda a: parse_base(a, '>q')
    quint64 = lambda a: parse_base(a, '>Q')
    qdouble = lambda a: parse_base(a, '>d')

    def qdatetime(a):
        return(quint64(a),
               qint32(a),
               (ts := qint8(a)),
               (qint32(a) if ts==2 else 0))

    def qutf8(a):
        i = 0 if (m:=quint32(a)) == 0xffffffff else m
        a._index = (o:=a._index) + i
        return '' if i == 0 else a.raw[o:a._index].decode()

    def qcolor(a):
        return (quint8(a),
                quint16(a),
                quint16(a),
                quint16(a),
                quint16(a),
                quint16(a))
        
    HEADER_FIELDS = (('magic',  quint32),
                     ('schema', quint32),
                     ('msg_id', quint32),
                     ('id_',    qutf8))

    decode_fields = (
        #HEARTBEAT
        (('max_schema', quint32),
        ('version',     qutf8),
        ('revision',    qutf8)),
        
        #STATUS
        (('dial_freq',   quint64),
        ('mode',         qutf8),
        ('dx_call',      qutf8),
        ('report',       qutf8),
        ('tx_mode',      qutf8),
        ('tx_enabled',   qbool),
        ('transmitting', qbool),
        ('decoding',     qbool),
        ('rx_df',        quint32),
        ('rx_df',        quint32),
        ('de_call',      qutf8),
        ('de_grid',      qutf8),
        ('dx_grid',      qutf8),
        ('tx_watchdog',  qbool),
        ('sub_mode',     qutf8),
        ('fast_mode',    qbool),
        ('spec_mode',    quint8),
        ('freq_tol',     quint32),
        ('tr_period',    quint32),
        ('conf_name',    qutf8),
        ('tx_msg',       qutf8)),

        #DECODE
        (('new',       qbool),
        ('time',       quint32),
        ('snr',        qint32),
        ('delta_time', qdouble),
        ('delta_freq', quint32),
        ('mode',       qutf8),
        ('message',    qutf8),
        ('low_conf',   qbool),
        ('off_air',    qbool)),

        # CLEAR_FIELDS = (('window', quint8),)
        ##def clear(a):
        ##    if len(a.raw) > a.index:
        ##        a.window = quint8(a)

        #CLEAR
        (),
        
        #REPLY
        (('time',      quint32),
        ('snr',        qint32),
        ('delta_time', qdouble),
        ('delta_freq', qint32),
        ('mode',       qutf8),
        ('message',    qutf8),
        ('low_conf',   qbool),
        ('modifiers',  quint8)),
        
        #LOG
        (('time_off', qdatetime),
        ('dx_call',   qutf8),
        ('dx_grid',   qutf8),
        ('tx_freq',   quint64),
        ('mode',      qutf8),
        ('rst_sent',  qutf8),
        ('rst_recv',  qutf8),
        ('tx_power',  qutf8),
        ('comments',  qutf8),
        ('name',      qutf8),
        ('time_on',   qdatetime),
        ('op_call',   qutf8),
        ('my_call',   qutf8),
        ('my_grid',   qutf8),
        ('ex_sent',   qutf8),
        ('ex_recv',   qutf8),
        ('adif_md',   qutf8)),
        
        #CLOSE
        (),
        
        #REPLAY
        (),
        
        #HALT_TX
        (('auto_tx_only', qbool),),
        
        #FREE_TEXT
        (('text', qutf8),
        ('send',  qbool)),
        
        #WSPR
        (('new_',      qbool),
        ('time',       quint32),
        ('snr',        qint32),
        ('delta_time', qdouble),
        ('freq',       quint64),
        ('drift',      quint32),
        ('callsign',   qutf8),
        ('grid',       qutf8),
        ('power',      qint32),
        ('off_air',    qbool)),

        #LOCATION -- note AutoGrid must be checked in WSJT-X 
        (('location', qutf8),),
        
        #ADIF
        (('text', qutf8),),
        
        #HIGHLIGHT CALLSIGN
        (('call',     qutf8),
        ('bg',        qcolor),
        ('fg',        qcolor),
        ('last_only', qbool)),

        #SWITCH CONFIGURATION
        (('conf_name', qutf8),),
        
        #CONFIGURE
        (('mode',     qutf8),
        ('freq_tol',  quint32),
        ('submode',   qutf8),
        ('fastmode',  qbool),
        ('tr_period', quint32),
        ('rx_df',     quint32),
        ('dx_call',   qutf8),
        ('dx_grid',   qutf8),
        ('gen_msg',   qbool)),
    )
    
    def do_fields(a, fields):
        for n,t in fields:
            a.__dict__[n] = t(a)
            
    class Data:
        pass
            
    a = Data()
    a._index = 0
    a.raw = d
    do_fields(a, HEADER_FIELDS)
    do_fields(a, decode_fields[a.msg_id])
    del a._index
    return a


if __name__ == '__main__':
    from sample_data.small_sample import SAMPLE_DATA
    # a = [parse(i) for i in SAMPLE_DATA.values()]
    a = parse(SAMPLE_DATA[12])
