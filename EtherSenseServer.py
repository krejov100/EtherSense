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

def getDepthAndTimestamp(pipeline, depth_filter):
    frames = pipeline.wait_for_frames()
    # take owner ship of the frame for further processing
    frames.keep()
    depth = frames.get_depth_frame()
    if depth:
        depth2 = depth_filter.process(depth)
        # take owner ship of the frame for further processing
        depth2.keep()
        # represent the frame as a numpy array
        depthData = depth2.as_frame().get_data()        
        depthMat = np.asanyarray(depthData)
        ts = frames.get_timestamp()
        return depthMat, ts
    else:
        return None, None

def openPipeline():
    cfg = rs.config()
    cfg.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
    pipeline = rs.pipeline()
    pipeline_profile = pipeline.start(cfg)
    sensor = pipeline_profile.get_device().first_depth_sensor()
    return pipeline

		
class EtherSenseServer(asyncore.dispatcher):
    def __init__(self, address):
        asyncore.dispatcher.__init__(self)
        print("Launching Realsense Camera Server")
        try:
            self.pipeline = openPipeline()
        except:
            print("Unexpected error: ", sys.exc_info()[1])
            sys.exit(1)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        client_address = (address[0], port)
        print('sending acknowledgement to', client_address)

	# reduce the resolution of the depth image using post processing
        self.decimate_filter = rs.decimation_filter()
        self.decimate_filter.set_option(rs.option.filter_magnitude, 2)
        self.frame_data = ''
        self.connect(client_address)
        self.packet_id = 0        

    def handle_connect(self):
        print("connection received")

    def writable(self):
        return True

    def update_frame(self):
        depth, timestamp = getDepthAndTimestamp(self.pipeline, self.decimate_filter)
        if depth is not None:
        # convert the depth image to a string for broadcast
            data = pickle.dumps(depth)
        # capture the lenght of the data portion of the message	
            length = struct.pack('<I', len(data))
        # include the current timestamp for the frame
            ts = struct.pack('<d', timestamp)
        # for the message for transmission
            self.frame_data = b''.join([length, ts, data])

    def handle_write(self):
        # first time the handle_write is called
        if not hasattr(self, 'frame_data'):
            self.update_frame()
        # the frame has been sent in it entirety so get the latest frame
        if len(self.frame_data) == 0:
            self.update_frame()
        else:
	    # send the remainder of the frame_data until there is no data remaining for transmition
            remaining_size = self.send(self.frame_data)
            self.frame_data = self.frame_data[remaining_size:]
	

    def handle_close(self):
        self.close()
            

class MulticastServer(asyncore.dispatcher):
    def __init__(self):
        asyncore.dispatcher.__init__(self)
        # Listen only to a multicast group.
        server_address = ('', port)
        self.create_socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.bind(server_address)
        # Join a multicast group on a local interface.
        mreq = struct.pack("4sl", socket.inet_aton(mc_ip_address), socket.INADDR_ANY)
        self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    def handle_read(self):
        data, addr = self.socket.recvfrom(42)
        print('Recived Multicast message %s bytes from %s' % (data, addr))
	# Once the server recives the multicast signal, open the frame server
        server = EtherSenseServer(addr)
        print(sys.stderr, data)

    def writable(self): 
        return False # don't want write notifies

    def handle_close(self):
        self.close()


def main(argv):
    # initalise the multicast receiver 
    MulticastServer()
    # hand over excicution flow to asyncore
    asyncore.loop()
   
if __name__ == '__main__':
    main(sys.argv[1:])