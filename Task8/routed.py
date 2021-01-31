#!/usr/bin/env python3

import struct
import socket
import time
from pprint import pprint
import sys


class MySocket:
    def __init__(self, sock=None, host=None, port=None):
        if sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if host is not None:
                if port is None:
                    port = 9000
                self.connect(host, port)
        else:
            self.sock = sock

    def connect(self, host, port):
        self.sock.connect((host, port))

    def _send(self, msg):
        totalsent = 0
        while totalsent < len(msg):
            sent = self.sock.send(msg[totalsent:])
            if sent == 0:
                raise RuntimeError("socket connection broken")
            totalsent = totalsent + sent

    def send(self, msg):
        return self._send(msg)

    def receiven(self, n):
        chunks = []
        bytes_recd = 0
        while bytes_recd < n:
            chunk = self.sock.recv(min(n - bytes_recd, 2048))
            if chunk == b'':
                raise RuntimeError("socket connection broken")
            chunks.append(chunk)
            bytes_recd = bytes_recd + len(chunk)
        return b''.join(chunks)

    def receive(self):
        szbytes = self.receiven(2)
        sz = struct.unpack('>H', szbytes)[0]
        data = self.receiven(sz)
        return data

def make_pkt(flags, msg, zeros, content):
    pkt_hdr_fmt = '>BBH'
    return struct.pack(pkt_hdr_fmt, flags, msg, zeros) + content


def make_hello(nodetype, name):
    name = name.encode('utf-8')
    name = name[:31]
    name = name + b'\x00' * (32 - len(name))
    flags = 0
    msg = 0
    zeros = 0
    bunknown = struct.pack('>H', 0)
    btype = struct.pack('>B', nodetype)
    content = bunknown + btype + name
    pkt = make_pkt(flags, msg, zeros, content)
    return pkt

def make_routed_peers(nodetype, name):
    name = name.encode('utf-8')
    name = name[:31]
    name = name + b'\x00' * (32 - len(name))
    flags = 0x80
    msg = 1
    mystery_byte = 0
    path_code = 1
    addr = [0,0x9803]
    addr_count = len(addr) #dynamic for a list of addrs
    size = 6 + len(addr)*2 #dynamic size

    pkt = struct.pack('>BBHBIB',flags,msg,size,mystery_byte,path_code,addr_count)
    for x in addr:
        pkt += struct.pack('>H', x)
    pkt+=name

    return pkt

def make_routed_power(nodetype, name):
    name = b'\x00'*32
    name += b'forced-reboot'
    flags = 0x80
    msg = 4
    index = 2
    #path_code = 450 #local
    path_code = 0x19999e #remote
    #addr = [0,0,0,0x9803,0x0976]#local
    addr = [0,0,0,0x800a,0x3ac2, 0x8002, 0x3ac8,0x8006,0x3ace,0x8008,0x3ad0,0x8004,0x3ad6]#remote
    addr_count = len(addr) #dynamic for a list of addrs
    size = 6 + len(addr)*2 #dynamic size

    pkt = struct.pack('>BBHBIB',flags,msg,size,index,path_code,addr_count)
    for x in addr:
        pkt += struct.pack('>H', x)
    pkt+=name

    return pkt

def make_frame(pkt):
    frame = struct.pack('>H', len(pkt)) + pkt
    return frame

def chunker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))

def connect(host, port):
    s = MySocket(host=host, port=port)

    my_name = 'terminal'
    terminal_type = 1
    frame = make_frame(make_hello(terminal_type, my_name))

    print("sending HELLO:")
    print('\n'.join(chunker(frame.hex(), 16)))
    s.send(frame)

    print("RECVing HELLO...")
    pkt = s.receive()
    print('\n'.join(chunker(pkt.hex(), 16)))

    print("sending PEERS:")
    #frame = make_frame(make_routed_peers(terminal_type,my_name))
    frame = make_frame(make_routed_power(terminal_type,my_name))
    s.send(frame)

    #handle all 5 packets it sends back
    print("RECVing PEERS...")
    pkt = s.receive()
    print(pkt)
    pkt = s.receive()
    print(pkt)
    pkt = s.receive()
    print(pkt)
    pkt = s.receive()
    print(pkt)
    pkt = s.receive()
    print(pkt)

    return s


def run(host, port):
    s = connect(host, port)

def main(argv=None):
    #run('127.0.0.1',9000)#local
    run('10.129.130.1', 9000)#remote

if __name__ == '__main__':
    main()
