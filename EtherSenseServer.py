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
#rs.log_to_console(rs.log_severity.debug)

def getDepthAndTimestamp(pipeline, depth_filter):
    frames = pipeline.wait_for_frames()
    frames.keep()
    depth = frames.get_depth_frame()
    if depth:
	depth2 = depth_filter.process(depth)
	depth2.keep()
        depthData = depth2.as_frame().get_data()        
        depthMat = np.asanyarray(depthData)
	ts = frames.get_timestamp()
        return depthMat, ts
    else:
        return None, None
def openBagPipeline(filename):
    cfg = rs.config()
    cfg.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
    #cfg.enable_device_from_file(filename)
    pipeline = rs.pipeline()
    pipeline_profile = pipeline.start(cfg)
    sensor = pipeline_profile.get_device().first_depth_sensor()
    #sensor.set_option(rs.option.emitter_enabled, 0)
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
        try:
            self.pipeline = openBagPipeline("/home/node1/Desktop/20181119_131946.bag")
        except:
            print("Unexpected error: ", sys.exc_info()[1])
            sys.exit(1)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        print('sending acknowledgement to', address)
        
        self.decimate_filter = rs.decimation_filter()
        self.decimate_filter.set_option(rs.option.filter_magnitude, 4)
        self.ready = True
        self.frameID = 0
        self.frame_data = ''
        self.connect((address[0], 1024))
        self.packet_id = 0        

    def handle_connect(self):
        print("connection received")

    def writable(self):
        return True

    def update_frame(self):
	depth, timestamp = getDepthAndTimestamp(self.pipeline, self.decimate_filter)
        if depth is not None:
            data = pickle.dumps(depth)
            length = struct.pack('<I', len(data))
            ts = struct.pack('<d', timestamp)
            self.frame_data = ''.join([length, ts, data])

    def handle_write(self):
        if not hasattr(self, 'frame_data'):
            self.update_frame()
        if len(self.frame_data) == 0:
	    self.update_frame()
        else:
            remaining_size = self.send(self.frame_data)
            self.frame_data = self.frame_data[remaining_size:]
	

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

