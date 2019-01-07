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


def getDepthAndColorMat(pipeline):
    frames = rs.composite_frame(rs.frame())
    frames = pipeline.poll_for_frames()
    if frames.size() > 0:
        depth = frames.get_depth_frame()
        depthData = depth.as_frame().get_data()
        depthMat = np.asanyarray(depthData)
        return depthMat

def openBagPipeline(filename):
    cfg = rs.config()
    cfg.enable_device_from_file(filename)
    pipeline = rs.pipeline()
    pipeline.start(cfg)
    return pipeline


class RealSenseUDPserver(asyncore.dispatcher):
    import pyrealsense2 as rs
    def __init__(self, address):
        asyncore.dispatcher.__init__(self)
        print("Launching Realsense Camera Server")
        self.create_socket(socket.AF_INET, socket.SOCK_DGRAM)
        print('sending acknowledgement to', address)
        self.connect(address)
        self.socket.send('ack'.encode())
        self.pipeline = openBagPipeline("/home/node1/Desktop/20181119_131946.bag")
        self.ready = True

    def writable(self):
        return hasattr(self,'pipeline')
    

    def handle_write(self):
        depth = getDepthAndColorMat(self.pipeline)
        if depth is not None:
            smallDepth = cv2.resize(depth, (0,0), fx=0.15, fy=0.15) 
            data = pickle.dumps(smallDepth)
            print(len(data))
            while data:
                data = data[self.socket.send(data):]        


class AsyncoreMulticastServer(asyncore.dispatcher):
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


#UDP client for each camera server 
class RealSenseUDPclient(asyncore.dispatcher):
    def __init__(self, port):
        asyncore.dispatcher.__init__(self)
        print('recived acknowledgement from', port)
        print("Launching Realsense Camera Client")
        self.create_socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(0.5)
        self.bind(('',port))
        self.socket.sendall("test")
    def writable(self): 
        return False
    
    def handle_read(self):
        data, server = sock.recvfrom(65507)
        ts, imdata = data[:struct.calcsize('d')], data[struct.calcsize('d'):]
        timestamp = struct.unpack('d', ts)
        imdata = pickle.loads(imdata)
        bigDepth = cv2.resize(imdata, (0,0), fx=2, fy=2, interpolation=cv2.INTER_NEAREST) 
        cv2.putText(bigDepth, str(timestamp), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (65536), 2, cv2.LINE_AA)
        cv2.imshow(str(server[1]), bigDepth)
        cv2.waitKey(1)

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
        print('test')
        if not self.connected:
            return True
        print("writable"+ self.signalUpdate)
        return self.signalUpdate

    def handle_write(self):
        print('Sending Toggle')
        self.send(self.signalUpdate)
        self.signalUpdate = False

       
def lasercallback(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONUP:
        print('click')
        param.toggle_laser()
        

def multi_cast_message(ip_address, port, message):
    multicast_group = (ip_address, port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(0.5)
    connections = {}

    try:
        # Send data to the multicast group
        print('sending "%s"' % message + str(multicast_group))
        sent = sock.sendto(message.encode(), multicast_group)

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
