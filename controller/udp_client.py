import socket
from struct import pack
from threading import Thread

from model.model import model
from model.event import ProcessID, Callback

class UDPClientController:
    def __init__(self):
        self.address = model.gps_address
        self.thread = Thread()
        self.do_close = False
        model.add_event_listener(Callback.GPS_SEND, self.send)

    def report(self, open_):
        model.notify_state(ProcessID.GPS, open_)        

    def close_socket(self):
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        self.sock.close()
        self.report(False)

    def start(self):
        if not self.thread.is_alive():
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.settimeout(2.0)
                self.sock.connect(self.address)
                self.thread = Thread(target=self.run)
                self.thread.start()
                self.report(True)
            except OSError:
                self.close_socket()
        
    def send(self, data):
        if not self.sock._closed:
            self.sock.sendall(data)

    def stop(self):
        if self.thread.is_alive():
            self.thread.join()
        
    def run(self):
        while model.running:
            try:
                if self.do_close:
                    self.do_close = False
                    break
                data = self.sock.recv(2048)
                model.process(ProcessID.GPS, data)
            except TimeoutError:
                continue
            except OSError as e:
                print(e)
                break
        self.close_socket()


if __name__ == '__main__':
    gps = UDPClientController(ProcessID.GPS,
                              model.settings.gps_address,
                              Callback.GPS_SEND)
    gps.start()
