#!/bin/env python2

from Queue import Queue
from socket import *
from threading import Thread
import select
import signal
import struct
import sys

broadcastPort = 6000
#broadcastMulticastGroup = '224.1.1.1'
#broadcastMulticastGroup = '239.255.255.255'
broadcastMulticastGroup = '239.255.42.42'

stop_threads = False

def printHex(data):
    print " ".join(hex(ord(n)) for n in data)

def broadcastListener(out_q, done):
    s = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
    s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    s.bind(('', broadcastPort))

    # join a multicast group
    mreq = struct.pack("4sl", inet_aton(broadcastMulticastGroup), INADDR_ANY)
    s.setsockopt(IPPROTO_IP, IP_ADD_MEMBERSHIP, mreq)

    s.setblocking(0)
    print "Listening for devices..."
    while not done():
        r_rdy, w_rdy, x_rdy  = select.select([s],[],[], 0.1)
        if r_rdy:
            msg = r_rdy[0].recv(128) 
            printHex(msg)
            out_q.put(msg)
    s.close()

def signal_handler(signal, frame):
    global stop_threads
    print "Exiting due to CTRL-C"
    stop_threads = True
    sys.exit(0)

class IPTV_DeviceControl:
    _knockPort = 9002
    _controlPort = 9001
    _connected = False
    def __init__(self, ip):
        self._ip = ip
    
    def connect(self):
        try:
            self._s = socket(AF_INET, SOCK_STREAM)
            print "Connecting to %s, %d" % (self._ip, self._controlPort)
            res = self._s.connect_ex((self._ip, self._controlPort))
            if res == 0:
                self._connected = True;
                self._my_ip = self._s.getsockname()[0]
        except:
            return False
        return res == 0

    def knock(self):
        pass    
    def GetName(self):
        if not self._connected:
            raise Exception('Not connected!')


        msg = 'IPTV_CMD'
        msg += struct.pack(">4shhhhBB", inet_aton(self._my_ip), self._controlPort, 0x7400, 0x1f00, 0x0221, 0, 0) # last 0 is a checksum
        printHex(msg)
        print len(msg)
        self._s.send(msg)
        resp = self._s.recv(128)
        print "recv:"
        printHex(resp)

if __name__ == '__main__':
    # register SIGINT handler to exit
    signal.signal(signal.SIGINT, signal_handler)

    q = Queue()
    listen_thread = Thread(target=broadcastListener, args=(q, lambda: stop_threads))
    listen_thread.start()

    d = IPTV_DeviceControl('10.10.10.187')
    print d.connect()
    d.GetName()
    while True:
        signal.pause()

