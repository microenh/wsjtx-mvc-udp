from threading import Thread
from serial import Serial, SerialException, PortNotOpenError, LF

from library.manager import manager

class SerialBase:
    def __init__(self, port, baud, expected=LF):
        self.ser = Serial(None,
                          baud,
                          timeout=2.0,
                          write_timeout=1.0)
        self.expected = expected
        self.ser.port = port
        self.thread = Thread()

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
            
    def push(self, id_, data=None):
        manager.push(id_, data)

    def stop(self):
        self.ser.close()
        if self.thread.is_alive():
            self.thread.join()

    def send(self, data):
        if self.ser.is_open:
            try:
                with manager.lock:
                    self.ser.write(data)
            except SerialException:
                self.ser.close()

    def run(self):
        expected = self.expected
        ser = self.ser
        while manager.running:
            if not ser.is_open:
                break
            try:
                data = ser.read_until(expected)
                if data[-1:] != expected:
                    # print('runt')
                    continue
                self.process(data)
            except (SerialException, TypeError):
                ser.close()
                break
        self.report(False)


if __name__ == '__main__':
    from main import main
    main()
