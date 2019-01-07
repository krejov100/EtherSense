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
    def __init__(self):
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
    
    def handle_close(self):
        self.close()

    
    def handle_read(self):
        print("handle_read")    
        print(self.recv(8192))


class RealSenseUDPserver(asyncore.dispatcher):
    def __init__(self, address):
        asyncore.dispatcher.__init__(self)
        print("Launching Realsense Camera Server")
        self.create_socket(socket.AF_INET, socket.SOCK_DGRAM)
        print('sending acknowledgement to', address)
        self.connect(address)
        self.pipeline = openBagPipeline("/home/node1/Desktop/20181119_131946.bag")
        self.ready = True


    def writable(self):
        return hasattr(self,'pipeline')

    def handle_write(self):
        depth, timestamp = getDepthAndTimestamp(self.pipeline)
        if depth is not None:
            smallDepth = cv2.resize(depth, (0,0), fx=0.15, fy=0.15, interpolation=cv2.INTER_NEAREST) 
            ts = struct.pack('d', timestamp)
            data = pickle.dumps(smallDepth)
            self.socket.sendall(ts + data)
            

class MulticastServer(asyncore.dispatcher):
    def __init__(self, host = mc_ip_address, port=1024):
        asyncore.dispatcher.__init__(self)
        server_address = ('', port)
        self.create_socket(socket.AF_INET, socket.SOCK_DGRAM)
        group = socket.inet_aton(host)
        mreq = struct.pack('4sL', group, socket.INADDR_ANY)
        self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.bind(server_address) 	

    def handle_read(self):
        data, addr = self.socket.recvfrom(42)
        print('received %s bytes from %s' % (data, addr))
        RealSenseUDPserver(addr)
        print(sys.stderr, data)

    def writable(self): 
        return False # don't want write notifies

    def handle_accept(self):
        channel, addr = self.accept()
        print('received %s bytes from %s' % (data, addr))


def main(argv):
    try:
        opts, args = getopt.getopt(argv, "hs", ["is_server="])
    except getopt.GetoptError:
        print('test.py -i <inputfile> -o <outputfile>')
        sys.exit(2)

    is_server = False
    for opt, arg in opts:
        if opt == '-h':
            print
            'test.py -s <is_server>'
            sys.exit()
        elif opt in ("-s"):
            is_server = True
        elif opt in ("--is_server"):
            is_server = arg
    print('is running as server -', is_server)
    if is_server:
        se = RealSenseSignalingServer()
        server = MulticastServer()
        asyncore.loop()
    else:
        run_client()

def run_server():
    # wait for a ping request
    wait_for_multi_cast(mc_ip_address, port);

def run_client():
    multi_cast_message(mc_ip_address, port, 'EtherSensePing')

def init_ip_address():
    pass

def wait_for_multi_cast(ip_address, port):
    server_address = ('', port)

    # Create the socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Bind to the server address
    #?sock.bind(server_address)?

    group = socket.inet_aton(ip_address)
    mreq = struct.pack('4sL', group, socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Create the socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Bind to the server address
    sock.bind(server_address)

    # Receive/respond loop
    while True:
        print('\nwaiting to receive message')
        data, address = sock.recvfrom(0)
        
        print('received %s bytes from %s' % (len(data), address))
        print(sys.stderr, data)

        print('sending acknowledgement to', address)
        sock.sendto('RSack', address)

def multi_cast_message(ip_address, port, message):
    multicast_group = (ip_address, port)
    #send out regular request for servers on network
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(0.2)
    # Set the time-to-live for messages to 1 so they do not go past the
    # local network segment.
    ttl = struct.pack('b', 1)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
    try:
        # Send data to the multicast group
        print('sending "%s"' % message + str(multicast_group))
        sent = sock.sendto(message.encode(), multicast_group)

        # Look for responses from all recipients
        while True:
            print('waiting to receive')
            try:
                data, server = sock.recvfrom(42)
            except socket.timeout:
                print('timed out, no more responses')
                break
            else:
                print('received "%s" from %s' % (data, server))
                

    finally:
        print(sys.stderr, 'closing socket')
        sock.close()

if __name__ == '__main__':
    main(sys.argv[1:])
