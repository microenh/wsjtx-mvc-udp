import socket
from struct import pack
from threading import Thread
from library.manager import manager

class UDPServerBase:
    def __init__(self, address):
        self.addr = None
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.settimeout(1.0)
        self.thread = Thread(target=self.run)
        host = address[0]
        if int(host.split('.')[0]) in range(224,240):
            mreq = pack("4sii",
                       socket.inet_aton(host),
                       socket.INADDR_ANY, 0)
            self.sock.setsockopt(socket.IPPROTO_IP,
                                 socket.IP_ADD_MEMBERSHIP,
                                 mreq)
            host = ''
        self.sock.bind(address)

    def start(self):
        self.thread.start()

    def send(self, data):
        if self.addr is not None:
            self.sock.sendto(data, self.addr)

    def push(self, id_, data=None):
        manager.push(id_, data)

    def stop(self):
        self.thread.join()
        
    def run(self):
        self.report(True)
        while manager.running:
            try:
                data, self.addr = self.sock.recvfrom(1024)
                # print(data)
                # print()
                self.process(data)
            except TimeoutError:
                # print('timeout')
                continue
        self.report(False)

