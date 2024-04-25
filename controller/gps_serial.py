from threading import Thread
from serial import Serial, SerialException, PortNotOpenError, LF
from model.event import ProcessID, Callback

from model.model import model

class GPSSerial:
    def __init__(self):
        self.ser = Serial(None,
                          9600,
                          timeout=2.0,
                          write_timeout=1.0)
        self.expected = LF
        self.ser.port = model.gps_serial_address
        self.thread = Thread()
        model.add_event_listener(Callback.GPS_SERIAL_SEND, self.send)


    def report(self, open_):
        model.notify_state(ProcessID.GPS_SERIAL, open_)        

    def start(self):
        if self.thread.is_alive():
            return
        try:
            self.ser.open()
            self.thread = Thread(target=self.run)
            self.thread.start()
            self.report(True)
        except SerialException:
            self.report(False)
            
    def stop(self):
        self.ser.close()
        if self.thread.is_alive():
            self.thread.join()

    def send(self, data):
        if self.ser.is_open:
            try:
                self.ser.write(data)
            except SerialException:
                self.ser.close()

    def run(self):
        expected = self.expected
        ser = self.ser
        while model.running:
            if not ser.is_open:
                break
            try:
                data = ser.read_until(expected)
                if data[-1:] != expected:
                    # print('runt')
                    continue
                model.process(ProcessID.GPS_SERIAL, data)
            except (SerialException, TypeError):
                ser.close()
                break
        self.report(False)


if __name__ == '__main__':
    from main import main
    main()
