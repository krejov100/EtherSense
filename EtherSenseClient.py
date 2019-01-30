#!/usr/bin/python
import pyrealsense2 as rs
import sys, getopt
import asyncore
import numpy as np
import pickle
import socket
import struct
import cv2


print('Number of arguments:', len(sys.argv), 'arguments.')
print('Argument List:', str(sys.argv))
mc_ip_address = '224.0.0.1'
local_ip_address = '192.168.0.1'
port = 1024
chunk_size = 4096

def main(argv):
    multi_cast_message(mc_ip_address, port, 'EtherSensePing')
        

#UDP client for each camera server 
class ImageClient(asyncore.dispatcher):
    def __init__(self, server, source):   
        asyncore.dispatcher.__init__(self, server)
        self.address = server.getsockname()[0]
        self.port = source[1]
        self.buffer = bytearray()
        self.windowName = self.port
        cv2.namedWindow("window"+str(self.windowName))
        self.remainingBytes = 0
        self.frame_id = 0
        #print('adding signelingClient')
        #signalServer = RealSenseSignalingClient(self.address)
        #cv2.setMouseCallback(self.windowName, lasercallback, param=signalServer)

    def handle_read(self):
        if self.remainingBytes == 0:
            self.frame_length = struct.unpack('<I', self.recv(4))[0]
            self.timestamp = struct.unpack('<d', self.recv(8))
            self.remainingBytes = self.frame_length
                
        data = self.recv(self.remainingBytes)
        self.buffer += data
        self.remainingBytes -= len(data)
        if len(self.buffer) == self.frame_length:
            self.handle_frame()

    def handle_frame(self):
        imdata = pickle.loads(self.buffer)
        bigDepth = cv2.resize(imdata, (0,0), fx=2, fy=2, interpolation=cv2.INTER_NEAREST) 
        cv2.putText(bigDepth, str(self.timestamp), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (65536), 2, cv2.LINE_AA)
        cv2.imshow("window"+str(self.windowName), bigDepth)
        cv2.waitKey(1)
        self.buffer = bytearray()
        self.frame_id += 1
    def readable(self):
        return True

class RealSenseSignalingClient(asyncore.dispatcher):
    def __init__(self,address):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect(('10.0.2.4',9006))
        print('connected')
        self.laserOn = True
        self.signalUpdate = False

    def toggle_laser(self):
        print('Toggling Laser')
        self.laserOn = not self.laserOn    
        self.signalUpdate = True

    def handle_connect(self):
        pass
    
    def handle_close(self):
        self.close()

    def writable(self):
        #if not self.connected:
        #    return True
        return self.signalUpdate

    def handle_write(self):
        print('Sending Toggle')
        self.send(struct.pack('?', self.laserOn))
        self.signalUpdate = False

       
def lasercallback(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONUP:
        print('click')
        param.toggle_laser()
        
class EtherSenseClient(asyncore.dispatcher):
    def __init__(self):
        asyncore.dispatcher.__init__(self)
        self.server_address = ('', 1024)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(5)
        
        self.bind(self.server_address) 	
        self.listen(10)

    def writable(self): 
        return False # don't want write notifies

    def readable(self):
        return True
        
    def handle_connect(self):
        print("connection recvied")

    def handle_accept(self):
        pair = self.accept()
        #print(self.recv(10))
        if pair is not None:
            sock, addr = pair
            print ('Incoming connection from %s' % repr(addr))
            handler = ImageClient(sock, addr)

def multi_cast_message(ip_address, port, message):
    multicast_group = (ip_address, port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    connections = {}
    try:
        # Send data to the multicast group
        print('sending "%s"' % message + str(multicast_group))
        sent = sock.sendto(message.encode(), multicast_group)
   
        client = EtherSenseClient()
        asyncore.loop()

        # Look for responses from all recipients
        
    except socket.timeout:
        print('timed out, no more responses')
    finally:
        print(sys.stderr, 'closing socket')
        sock.close()

if __name__ == '__main__':
    main(sys.argv[1:])
