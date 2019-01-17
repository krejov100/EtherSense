# install the dependancies from pip
try:
    from pip import main as pipmain
except:
    from pip._internal import main as pipmain
pipmain(['install', 'numpy'])
pipmain(['install', 'python-crontab'])
pipmain(['install', 'opencv-python'])
pipmain(['install', 'pyrealsense2'])
pipmain(['install', 'cron_descriptor'])

# using python-crontab, setup a job that is ran on the minute to check if the server is running. 
# https://pypi.org/project/python-crontab/
from crontab import CronTab
#using the system crontab file as sudo is required for librealsense aquisition
system_cron = CronTab(tabfile='/etc/crontab', user=False)
#requires the shell enviroment as ./AlwaysRunningServer.bash 
system_cron.env['SHELL'] = '/bin/bash'

#the cron job is cd to the EtherSense dir then run AlwaysRunningServer.bash, logging to /temp/error.log
#have to use this $(ls /home/) to find home dir, assuming no other user spaces.
job = system_cron.new(command='cd /home/$(ls /home/)/EtherSense; ./AlwaysRunningServer.bash > /tmp/error.log 2>&1', user='root')

# this line sets the frequance of server checking, stars for all time slices means every minute
job.setall('* * * * *')
system_cron.write()
print('cron job set to run ' + job.description())


