#!/bin/env python2

from Queue import Queue, Empty
from socket import *
from threading import Thread
import argparse
import select
import signal
import struct
import sys

broadcastPort = 6000
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

    ips = []
    s.setblocking(0)
    print "Listening for devices..."
    while not done():
        r_rdy, w_rdy, x_rdy  = select.select([s],[],[], 0.1)
        if r_rdy:
            msg = r_rdy[0].recv(128)
            ip1, ip2, ip3, ip4 = struct.unpack("BBBB", msg[2:6])
            ip = "%d.%d.%d.%d" % (ip1, ip2, ip3, ip4)
            if not ip in ips:
                print "Found device at %s" % ip
                ips.append(ip)
                out_q.put(ip)
    s.close()

def signal_handler(signal, frame):
    global stop_threads
    print "Exiting due to CTRL-C"
    stop_threads = True
    sys.exit(0)

class IPTV_DeviceControl:
    _controlPort = 9001
    def __init__(self, ip):
        self._ip = ip
    
    def __connect(self):
        sock = socket(AF_INET, SOCK_STREAM)
        ip = '0'
        try:
            res = sock.connect_ex((self._ip, self._controlPort))
            if res == 0:
                ip = sock.getsockname()[0]
        except Exception, e:
            print "Exception: %s" % e
            sock.close()
            return False, None, None
        return res == 0, sock, ip

    def __newTCPServer(self):
        sock = socket(AF_INET, SOCK_STREAM)
        sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        sock.bind(('', 0))
        return sock

    def __performCommand(self, msg):
        # connect to the remote device
        valid, remote_sock, my_ip = self.__connect()

        if not valid:
            print "Could not establish connection to the device"
            return False

        # start TCP server to catch response
        listen = self.__newTCPServer()
        listenPort = listen.getsockname()[1]
        listen.listen(1)

        # construct header
        payload = 'IPTV_CMD'
        payload += struct.pack(">4sH", inet_aton(my_ip), listenPort)

        # append message
        payload += msg

        # send payload
        #print "Sending"
        #printHex(payload)
        remote_sock.send(payload)

        # listen for response
        conn, addr = listen.accept()
        data = conn.recv(256)

        #TODO check checksum

        conn.close()
        listen.close()
        remote_sock.close()

        return data

    def GetName(self):
        # construct message
        msg = struct.pack(">HHHBB", 0x7400, 0x1f00, 0x0221, 0, 0) # last 0 is a checksum

        # perform command
        data = self.__performCommand(msg)
        if data:
            if len(data) != 53:
                print "Invalid length response of %d (should be 53)" % len(data)
                printHex(data)
                return None

            tmp = data[18:]
            resp, name, checksum = struct.unpack(">H32sB", tmp)
            return name
        return None

    def GetVersions(self):
        msg = struct.pack(">HHHBB", 0x7401, 0x0f00, 0x0212, 0, 0)

        data = self.__performCommand(msg)
        if data:
            if not ord(data[18]) == 0x41:
                print "Got invalid length %d (should be 65)" % ord(data[18])
                printHex(data)
                return None
            tmp = data[20:]
            fw_ver, encoder_ver, checksum = struct.unpack("32s32sB", tmp)
            return fw_ver, encoder_ver
        return None, None

    def reboot(self):
        msg = struct.pack(">HHHBB", 0x7400, 0xf000, 0x02f2, 0, 0)

        data = self.__performCommand(msg)
        if data:
            if not len(data) == 22:
                print "Got invalid length %d (should be 22)" % len(data)
                printHex(data)
                return False
            if not ord(data[18]) == 0x02 and not ord(data[19]) == 0xf3:
                print "Got invalid command response %s %s (expected 02 f3)" % (hex(ord(data[18])), hex(ord(data[19])))
                return False
            return True
        return False

def setupArgs():
    parser = argparse.ArgumentParser(description="LK373A compatible control utility")
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--ip', help="IP of device to manage")
    group.add_argument('-l', '--listen', help="Listen for units broadcasting their existence", action="store_true")
#    group.add_argument('-s', '--search', help="Search for units via UDP broadcast", action="store_true")
    parser.add_argument('-r', '--reboot', help="Reboot the device", action="store_true")

    return parser

if __name__ == '__main__':
    # register SIGINT handler to exit
    signal.signal(signal.SIGINT, signal_handler)

    parser = setupArgs()
    args = parser.parse_args()
    #print args

    # if we're not broadcasting and haven't been given an IP, listen
    if not args.ip:# and not args.search:
        args.listen = True

    q = Queue()

    if args.listen:
        listen_thread = Thread(target=broadcastListener, args=(q, lambda: stop_threads))
        listen_thread.start()

    if args.ip:
        q.put(args.ip)

    while True:
        try:
            ip = q.get(timeout=0.1)
            d = IPTV_DeviceControl(ip)
            name = d.GetName()
            if not name:
                print "Failed to get device name"
            else:
                print "Device name is %s" % name
            fw, codec = d.GetVersions()
            print "FW ver: %s\nCodec ver: %s" % (fw, codec)
            if args.reboot:
                d.reboot()
        except Empty:
            if args.ip:
                sys.exit(0)
            pass
  #  while True:
   #     signal.pause()

