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
        #print('adding signelingClient')
        #signalServer = RealSenseSignalingClient(self.address)
        #cv2.setMouseCallback(self.windowName, lasercallback, param=signalServer)

    def handle_read(self):
        self.buffer
        if len(self.buffer) == 0:
            self.timestamp = struct.unpack('d', self.recv(8))
            self.frame_length = struct.unpack('I', self.recv(4))[0]

      
        data = self.recv(int(self.frame_length))#
        self.buffer += data
        if len(self.buffer) == self.frame_length:
            self.handle_frame()

    def handle_frame(self):
        imdata = pickle.loads(self.buffer)
        bigDepth = cv2.resize(imdata, (0,0), fx=2, fy=2, interpolation=cv2.INTER_NEAREST) 
        cv2.putText(bigDepth, str(self.timestamp), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (65536), 2, cv2.LINE_AA)
        cv2.imshow("window"+str(self.windowName), bigDepth)
        cv2.waitKey(1)
        self.buffer = bytearray()
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
        
class EchoHandler(asyncore.dispatcher):

    def handle_read(self):
        data = self.recv(8192)
        if data:
          print(data)

class EtherSenseClient(asyncore.dispatcher):
    def __init__(self):
        asyncore.dispatcher.__init__(self)
        self.server_address = ('', 1024)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bind(self.server_address) 	
        self.listen(5)

    def writable(self): 
        return False # don't want write notifies

    def readable(self):
        return True

    def handle_read(self):
        print(self.recv(1024))

    def handle_connect(self):
        print("connection recvied")

    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            sock, addr = pair
            print ('Incoming connection from %s' % repr(addr))
            handler = ImageClient(sock, addr)






def multi_cast_message(ip_address, port, message):
    multicast_group = (ip_address, port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(0.5)
    connections = {}
    try:
        # Send data to the multicast group
        print('sending "%s"' % message + str(multicast_group))
        sent = sock.sendto(message.encode(), multicast_group)
   
        client = EtherSenseClient()
        asyncore.loop(timeout=5)

        return  #  finish
        # Look for responses from all recipients
        while True:
            try:
                data, server = sock.recvfrom(65507)
                ts, imdata = data[:struct.calcsize('d')], data[struct.calcsize('d'):]
                timestamp = struct.unpack('d', ts)
                imdata = pickle.loads(imdata)
                bigDepth = cv2.resize(imdata, (0,0), fx=2, fy=2, interpolation=cv2.INTER_NEAREST) 
                cv2.putText(bigDepth, str(timestamp), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (65536), 2, cv2.LINE_AA)
                windowName = str(server[1])
                cv2.namedWindow(windowName)
                if windowName not in connections:
                    print('adding signelingClient')
                    connections[windowName] = RealSenseSignalingClient(server[0])
                cv2.setMouseCallback(windowName, lasercallback, param=connections[windowName])
                cv2.imshow(windowName, bigDepth)
                cv2.waitKey(1)
            except socket.timeout:
                print('timed out, no more responses')
                break
    finally:
        print(sys.stderr, 'closing socket')
        sock.close()

if __name__ == '__main__':
    main(sys.argv[1:])
