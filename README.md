# EtherSense
Ethernet client and server for RealSense using python's Asyncore.

## Prerequisites
Installation and Setup of Server:
These steps assume a fresh install of Ubuntu 18.04 on an UpBoard but has also been tested on an Intel NUC.

$sudo apt-get update; sudo apt-get upgrade; 

$sudo apt-get install python

$sudo apt-get install python-pip  

$sudo apt-get install git 

Clone the repo then run:

$sudo python setup.py

This will first install the pip dependencies, followed by the creation of cronjobs in the /etc/crontab file that maintains an instance of the Server running whenever the device is powered. 

## Overview
Mulicast broadcast is used to establish connections to servers that are present on the network. 
Once a server receives a request for connection from a client, Asyncore is used to establish a TCP connection for each server. 
Frames are collected from the camera using librealsense pipeline. It is then resized and send in smaller chucks as to conform with TCP.

## Client Window
Below shows the result of having connected to two cameras over the local network: 
![Example Image](https://github.com/krejov100/EtherSense/blob/master/MultiCameraEthernet.jpg)
The window titles indicate the port which the frames are being received over. 

## Error Logging
Errors are piped to a log file stored in /tmp/error.log as part of the command that is setup in /etc/crontab

## NOTES
### Memory Leak due to Pickling Numpy Arrays
Currently there is a regression in numpy that is causing a memory leak on devices that run the Server script, to cricumvet this you can sudo pip install --upgrade numpy==1.15.4 to use an early version
See https://github.com/numpy/numpy/issues/12793 for more details

### Power Considerations
The upboards require a 5v 4Amp power supply, using PoE breakout adaptors I have found stability issues, for example the device kernal can crash when the HDMI port is connected, and so I recommend running the UpBoard as a headless server when using PoE. 

### Network bandwidth
It is currenlty very easy to saturate the bandwidth of the Ethernet connection I have tested 2 servers connected to the same clinent without issue, but find that cameras can dropout when 3 are used at the current transmition settings of:

cfg.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

self.decimate_filter.set_option(rs.option.filter_magnitude, 4)

There are a number of stratagies that can be used to increase this bandwidth but are left to the user for brevity and the specific tradeoff for your application, these include:

Transmitting frames using UDP and allowing for framedrop, this requires implimentation of packet orderering.

Reducing the depth channel to 8bit.

Reducing the Resoultion further. 

The addition of compression, either framewise or better still temporal. 

Local recording of the depth data into a buffer, with asynchronous frame transfer. 
