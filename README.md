# EtherSense
Ethernet client and server for RealSense using python's Asyncore.

Installation and Setup of Server:
These steps assume a fresh install of ubuntu 18.04 on an UpBoard but has also been tested on an Intel NUC.

##Prerequisites
$sudo apt-get update; sudo apt-get upgrade; 
$sudo apt-get install python
$sudo apt-get install python-pip  
$sudo apt-get install git 
Clone the repo then run:
$sudo python setup.py
This will first install the pip dependancies, followed by the creation of cronjobs in the /etc/crontab file that maintains an instance of the Server running whenever the device is powered. 

Mulicast broadcast is used to establish connections to servers that are present on the network. 
Once a server recives a request for connection from a client, Asyncore is used to establish a TCP conneciton for each server. 
Frames are collected from the camera using librealsense pipeline. It is then resized and send in smaller chucks as to conform with TCP.

Below shows the result of having connected to two cameras over the local network: 
![Example Image](https://github.com/krejov100/EtherSense/blob/master/MultiCameraEthernet.jpg)
The window titles indicate the port which the frames are being recived over. 
