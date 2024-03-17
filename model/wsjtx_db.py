"""store/query logged contacts"""
import os
import sqlite3
from datetime import datetime, timezone

try:
    from utility import lon_lat
    from rx_msg import to_datetime
except ModuleNotFoundError:
    from model.utility import lon_lat
    from model.rx_msg import to_datetime

class WsjtxDb:
    def __init__(self, settings):
        self.settings = settings
        CREATE_TABLES = ("""
            create table if not exists qsos (
                time_off int,
                dx_call text,
                dx_grid text,
                tx_freq int,
                mode text,
                rst_sent text,
                rst_recv text,
                tx_power text,
                comments text,
                name text,
                time_on real,
                op_call text,
                my_call text,
                my_grid text,
                ex_sent text,
                ex_recv text,
                adif_md text,
                ordinal_on int,
                band int,
                park text,
                shift text);
            """,
            """
            create unique index if not exists activator on qsos (
                dx_call,
                mode,
                ordinal_on,
                band,
                park,
                shift);
            """,
            """
            create unique index if not exists hunter on qsos (
                dx_call,
                mode,
                ordinal_on,
                band);
            """,
        )
        with sqlite3.connect(self.settings.dbn) as con:
            for i in CREATE_TABLES:
                con.execute(i)
            con.commit()
                
    def exists(self, dx_call, d):
        QUERY = """select exists(
            select 1 from qsos
                where dx_call=?
                and mode=?
                and ordinal_on=?
                and band=?
                and park=?
                and shift=?
            )"""
        with sqlite3.connect(self.settings.dbn) as con:
            return con.execute(QUERY, (
                dx_call,
                d.mode,
                self.settings.ordinal,
                self.settings.band,
                self.settings.park,
                self.settings.shift,
            )).fetchone()        

    def add(self, d):
        QUERY = """insert or replace into qsos(
                time_off,
                dx_call,
                dx_grid,
                tx_freq,
                mode,
                rst_sent,
                rst_recv,
                tx_power,
                comments,
                name,
                time_on,
                op_call,
                my_call,
                my_grid,
                ex_sent,
                ex_recv,
                adif_md,
                ordinal_on,
                band,
                park,
                shift
        ) values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""
        
        with sqlite3.connect(self.settings.dbn) as con:
            con.execute(QUERY, (
                to_datetime(*d.time_off).timestamp(),
                d.dx_call,
                d.dx_grid,
                d.tx_freq,
                d.mode,
                d.rst_sent,
                d.rst_recv,
                d.tx_power,
                d.comments,
                d.name,
                to_datetime(*d.time_on).timestamp(),
                d.op_call,
                d.my_call,
                d.my_grid,
                d.ex_sent,
                d.ex_recv,
                d.adif_md,
                self.settings.ordinal,
                self.settings.band,
                self.settings.park,
                self.settings.shift,
            ))
            con.commit()

    def add_log(self, text):
        exists = os.path.isfile(self.settings.adifn)
        with open(settings.adifn, 'a') as f:
            if exists:
                text = text.split('<EOH>\n')[1]
            f.write(text)

    def close(self):
        pass
