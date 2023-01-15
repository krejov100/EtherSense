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
depth_scale = 0.0010000000474974513
port = 1024
chunk_size = 4096

max_distance = 3.0 # m
min_distance = 0.3 # m

def main(argv):
    multi_cast_message(mc_ip_address, port, 'EtherSensePing')

def D2RGB(depth_map):
    # Convert depth map to float type
    d = depth_map.astype(np.float)

    # Initialize empty RGB image
    rgb = np.zeros((d.shape[0], d.shape[1], 3), dtype=np.uint8)

    # Compute RGB channels from depth map
    r = np.zeros_like(d)
    g = np.zeros_like(d)
    b = np.zeros_like(d)

    # Normalize depth
    d_normal = 1529.0 * (d - min_distance) / (max_distance - min_distance)
    d_normal = np.rint(d_normal)

    # D2R
    r[np.logical_or(d_normal < 255, 1275 <= d_normal)] = 255

    condition = np.logical_and(255 <= d_normal, d_normal < 510)
    r[condition] = (509 - d_normal)[condition]

    condition = np.logical_and(1020 <= d_normal, d_normal < 1275)
    r[condition] = (d_normal - 1020)[condition]

    # D2G
    condition = d_normal < 255
    g[condition] = d_normal[condition]

    g[np.logical_and(255 <= d_normal, d_normal < 765)] = 255

    condition = np.logical_and(765 <= d_normal, d_normal < 1020)
    g[condition] = (1019 - d_normal)[condition]

    # D2B
    condition = np.logical_and(510 <= d_normal, d_normal < 765)
    b[condition] = (d_normal - 510)[condition]

    b[np.logical_and(765 <= d_normal, d_normal < 1275)] = 255

    condition = 1275 <= d_normal
    b[condition] = (1529 - d_normal)[condition]

    # Set RGB channels to RGB image
    rgb[:,:,0] = r
    rgb[:,:,1] = g
    rgb[:,:,2] = b

    return rgb


#UDP client for each camera server 
class ImageClient(asyncore.dispatcher):
    def __init__(self, server, source):   
        asyncore.dispatcher.__init__(self, server)
        self.buffer = bytearray()
        self.windowName = source[1]
        # open cv window which is unique to the port 
        cv2.namedWindow("window"+str(self.windowName))
        self.remainingBytes = 0
        self.frame_id = 0
       
    def handle_read(self):
        if self.remainingBytes == 0:
            # get the expected frame size
            self.frame_length = struct.unpack('<I', self.recv(4))[0]
            # get the timestamp of the current frame
            self.timestamp = struct.unpack('<d', self.recv(8))
            self.remainingBytes = self.frame_length
        
        # request the frame data until the frame is completely in buffer
        data = self.recv(self.remainingBytes)
        self.buffer += data
        self.remainingBytes -= len(data)
        # once the frame is fully recived, process/display it
        if len(self.buffer) == self.frame_length:
            self.handle_frame()

    def handle_frame(self):
        # convert the frame from string to numerical data
        imdata = pickle.loads(self.buffer)
        bigDepth = cv2.resize(imdata, (0,0), fx=2, fy=2, interpolation=cv2.INTER_NEAREST)
        bigDepth = D2RGB(bigDepth * depth_scale)
        cv2.putText(bigDepth, str(self.timestamp), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (65536), 2, cv2.LINE_AA)
        cv2.imshow("window"+str(self.windowName), cv2.cvtColor(bigDepth, cv2.COLOR_RGB2BGR))
        cv2.waitKey(1)
        self.buffer = bytearray()
        self.frame_id += 1
    def readable(self):
        return True

    
class EtherSenseClient(asyncore.dispatcher):
    def __init__(self):
        asyncore.dispatcher.__init__(self)
        self.server_address = ('', port)
        # create a socket for TCP connection between the client and server
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

    def handle_accepted(self, sock, addr):
        if sock is not None:
            print ('Incoming connection from %s' % repr(addr))
            # when a connection is attempted, delegate image receival to the ImageClient 
            handler = ImageClient(sock, addr)

def multi_cast_message(ip_address, port, message):
    # send the multicast message
    multicast_group = (ip_address, port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Limit multicasting to local network.
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    
    try:
        client = EtherSenseClient()
        # Send data to the multicast group
        print('sending "%s"' % message + str(multicast_group))
        sock.sendto(message.encode(), multicast_group)
   
        # defer waiting for a response using Asyncore
        
        asyncore.loop()

        # Look for responses from all recipients
        
    except socket.timeout:
        print('timed out, no more responses')
    finally:
        print(sys.stderr, 'closing socket')
        sock.close()

if __name__ == '__main__':
    main(sys.argv[1:])
