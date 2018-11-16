#!/usr/bin/python

import sys, getopt
#import pyrealsense2 as rs
#import open3d
import socket
import struct



class AsyncoreSocketUDP(asyncore.dispatcher):
    def __init__(self, port=1024):
        self.dispatcher.__init__(self)
	self.create_socket(socket.AF_INET, socket.SOCK_DGRAM)
	self.bind(('10.0.2.5', port))
    def handle_read(self):
        data, addr = self.recvfrom(2048)
    def writable(self): 
        return False # don't want write notifies


print('Number of arguments:', len(sys.argv), 'arguments.')
print('Argument List:', str(sys.argv))
mc_ip_address = '224.0.0.1'
port = 1024


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
        run_server()
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
    sock.bind(server_address)

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
        data, address = sock.recvfrom(42)

        print('received %s bytes from %s' % (len(data), address))
        print(sys.stderr, data)

        print('sending acknowledgement to', address)
        sock.sendto('ack', address)

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
