import pexpect
import time
import re
import logging
from GetData import getData
from Buffer import flushBuffer
from loggerSetup import logToFile
from robot.api import logger
from robot.output import librarylogger
from robot.running.context import EXECUTION_CONTEXTS


def preSetup(image):
	
	data = getData('variable.json')								#Get the json data from file "variable.json"
	NumberOfDevices = data["NumberOfDevices"]
	device = pexpect.spawn("/bin/bash")							#Spawn the process ("/bin/bash")- Terminal
	logToFile.info("	  Pulling the flexswitch base image")
	device.expect(['/$',pexpect.EOF,pexpect.TIMEOUT],timeout=1)
	cmd = "sudo docker pull %s" %(image)
	device.sendline(cmd)									#Pull the flexswitch image from docker hub
	device.expect(['/w+@.*/#',pexpect.EOF,pexpect.TIMEOUT],timeout=2)
	device.expect(['/$',pexpect.EOF,pexpect.TIMEOUT],timeout=2)
	logToFile.info("	  Creating  directory for storing network namespace") 
	device.sendline("mkdir -m 777 -p /var/run/netns")					#Create a directory
	device.expect(['netns',pexpect.EOF,pexpect.TIMEOUT],timeout=2)
	logger.info(device.before,also_console=True)
	return device



def createNodes(iterator,device):                                 				#Instantiates a docker container that emulates a network device(say Router)

	i = iterator
	flushBuffer(1,device)
	device.sendcontrol('m')		
	device.expect(['/#',pexpect.EOF,pexpect.TIMEOUT],timeout=1)
	cmd = """sudo docker run -dt --privileged --log-driver=syslog --cap-add=ALL  --name Router%d -P snapos/flex:flex2""" %(i+1)    													#Instantiates the container	
	device.sendline(cmd)
	device.expect(['/d+',pexpect.EOF,pexpect.TIMEOUT],timeout=2)
	logger.info(device.before,also_console=True)
	flushBuffer(1,device)
	device.expect(['/w+@.*/#',pexpect.EOF,pexpect.TIMEOUT],timeout=1)
	cmd1 = """sudo docker inspect -f '{{.State.Pid}}' Router%d""" %(i+1)			#Gets PID for the container
	device.sendline(cmd1)
	device.expect(['/d+',pexpect.EOF,pexpect.TIMEOUT],timeout=8)
	logger.info(device.before,also_console=True)
	output = device.before
	pid = re.search('(\d\d[\d$]+)\s',output)						#Searches for the PID value
	return pid


def addLinks(device,intfList):									#Adds Links between devices

	flushBuffer(1,device)
	
	i = 0 ; j = 2
	maxiter =  len(intfList)
	while i != maxiter:

		cmd = """sudo ip link add %s type veth peer name %s""" %(intfList[i],intfList[i+1])
		device.sendline(cmd)
		device.expect(['w+@.*/#',pexpect.EOF,pexpect.TIMEOUT],timeout=8)
		logger.info(device.before,also_console=True)
		logToFile.info("		link Router1(%s)-----------------------------%s(Router%d)",intfList[i],intfList[i+1],j)
		i = i + 2
		j = j + 1
	return


def setInterfaceUp(device,RouterPid,intfList):							#Brings the interfaces up

	#flushBuffer(1,device)

	j = 0
	i = 1
	maxiter = len(intfList)
	while j != maxiter:
	
		if j % 2 == 0:
			
			flushBuffer(1,device)	
			cmd = """sudo ip link set %s netns %s
			sudo ip netns exec %s ip link set %s up""" %(intfList[j],RouterPid[0],RouterPid[0],intfList[j])
			device.sendline(cmd)
			device.expect(['w+@.*/#',pexpect.EOF,pexpect.TIMEOUT],timeout=3)
			logToFile.info('		Interface %s of Router1 UP',intfList[j])
			logger.info(device.before,also_console=True)
			j = j+1

		else:
			flushBuffer(1,device)
			cmd = """sudo ip link set %s netns %s
			sudo ip netns exec %s ip link set %s up""" %(intfList[j],RouterPid[i],RouterPid[i],intfList[j])
			device.sendline(cmd)
			device.expect(['w+@.*/#',pexpect.EOF,pexpect.TIMEOUT],timeout=3)
			logToFile.info('		Interface %s of Router%d UP',intfList[j],i+1) 
			logger.info(device.before,also_console=True)
			j = j+1
			i = i+1	

	return 
			
			

	

