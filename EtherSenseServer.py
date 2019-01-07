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

def getDepthAndTimestamp(pipeline):
    frames = rs.composite_frame(rs.frame())
    frames = pipeline.poll_for_frames()
    if frames.size() > 0:
        depth = frames.get_depth_frame()
        depthData = depth.as_frame().get_data()
        depthMat = np.asanyarray(depthData)
        return depthMat, frames.get_timestamp()
    else:
        return None, None
def openBagPipeline(filename):
    cfg = rs.config()
    cfg.enable_device_from_file(filename)
    pipeline = rs.pipeline()
    pipeline.start(cfg)
    return pipeline

class DevNullHandler(asyncore.dispatcher_with_send):

    def handle_read(self):
        print(self.recv(1024))

    def handle_close(self):
        self.close()

class RealSenseSignalingServer(asyncore.dispatcher):
    def __init__(self, address):
        #self.pipeline = pipeline
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind(('0.0.0.0', 9006))
        print(self.socket.getsockname()[1])
        self.listen(10)
        
    
    def handle_connect(self):
        print('connection')

    def handle_close(self):
        self.close()

    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            sock, addr = pair
            #print "Incoming connection from %s" % repr(addr)
            self.handler = DevNullHandler(sock)

        #pair = self.accept()
        #if pair is not None:
        #    sock, addr = pair
        #    print('Incoming Signaling from %s' % repr(addr))
        
    def handle_read(self):
        print("handle_read")    
        print(self.recv(8192))

            
class EtherSenseServer(asyncore.dispatcher):
    def __init__(self, address):
        asyncore.dispatcher.__init__(self)
        print("Launching Realsense Camera Server")
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        print('sending acknowledgement to', address)
        self.connect((address[0], 1024))
        self.pipeline = openBagPipeline("/home/node1/Desktop/20181119_131946.bag")
        self.ready = True
        self.frameID = 0

    def handle_connect(self):
        print("connection recvied")

    def writable(self):
        return True

    def handle_write(self):
        depth, timestamp = getDepthAndTimestamp(self.pipeline)
        if depth is not None:
            if self.frameID % 1== 0:
                smallDepth = cv2.resize(depth, (0,0), fx=0.15, fy=0.15, interpolation=cv2.INTER_NEAREST) 
                ts = struct.pack('d', timestamp)
                data = pickle.dumps(smallDepth)
                length = struct.pack('I', len(data))
                self.socket.send(ts+length+data)
        self.frameID += 1

    def handle_close(self):
        self.close()
            

class MulticastServer(asyncore.dispatcher):
    def __init__(self, host = mc_ip_address, port=1024):
        asyncore.dispatcher.__init__(self)
        server_address = ('', port)
        self.create_socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.bind(server_address) 	

    def handle_read(self):
        data, addr = self.socket.recvfrom(42)
        print('Recived Multicast message %s bytes from %s' % (data, addr))
        #RealSenseSignalingServer(addr)
        EtherSenseServer(addr)
        print(sys.stderr, data)

    def writable(self): 
        return False # don't want write notifies

    def handle_close(self):
        self.close()

    def handle_accept(self):
        channel, addr = self.accept()
        print('received %s bytes from %s' % (data, addr))


def main(argv):
    server = MulticastServer()
    asyncore.loop()
   
if __name__ == '__main__':
    main(sys.argv[1:])
