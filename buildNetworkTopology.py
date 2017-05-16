import pexpect
import time
import json
import re
import Topology
import logging
from Buffer import flushBuffer
from GetData import getData
from loggerSetup import logToFile
from robot.api import logger
from robot.output import librarylogger
from robot.running.context import EXECUTION_CONTEXTS


#The method takes argument that specifies type of topology to be built and then includes calls to several methods that aids in implementing operation of building the network
#	In it's preSetup(), it Pulls the latest flexswitch image from docker hub, creates directory for storing docker details, add symbolic links
#	In it's createNodes(), it instantiates docker container that emulates network device Router(Uses docker commands)
#	In it's addLink(), it adds link between devices(Uses Linux commands) 
#	In it's setInterfacesUP(), it brings up all the created interfaces (Uses Linux commands)

def buildNetwork(TopologyType,image):

	RouterPid = []
	data = getData('variable.json')
	NumberOfDevices = data["NumberOfDevices"]
	logToFile.info("	  Setting up the pre-requisite environment")
	device = Topology.preSetup(image)
	logToFile.info("	  Setting up the nodes of the network")

	for i in range(0,NumberOfDevices):						
	
		NodeID = Topology.createNodes(i,device)					 
		count = 3		
		while count >= 0:

			if NodeID:

				logToFile.info("		NODE CREATED(Router%d)",i+1)	
				RouterPid.append(NodeID.group(1))
				cmd = """ln -s /proc/%s/ns/net /var/run/netns/%s""" %(RouterPid[i],RouterPid[i])
				device.sendline(cmd)
				device.expect(['/d+',pexpect.EOF,pexpect.TIMEOUT],timeout=3)
				logger.info(device.before,also_console=True)
				break
			else:

				cmd = "sudo docker rm -f Router%d" %(i+1)
				device.sendline(cmd)
				NodeID = Topology.createNodes(i,device)
				count = count - 1 
				if count == -1:
					logToFile.debug("Unable to instantiate container for node creation")
					raise RuntimeError("Some error : Unable to instantiate docker container for Router") 
				else:
					continue


	logToFile.info("	  Adding links between routers")

	if TopologyType == 'Star':

		NumberOfInterfaces = (2 * NumberOfDevices) - 2 
		NumberOfNetworks = NumberOfDevices - 1
		intfList = []
		nwList = [] 
	
		for i in range(1,(NumberOfInterfaces+1)):
			intfList.append('eth' + str(i))

		for i in range(0,(NumberOfNetworks+1)):
			nwStart = data["Network"]
			nw = nwStart.split('/')
			nwOctets = nw[0].split('.')
			nwList.append(nwOctets[0] + '.' + nwOctets[1] + '.' + str(i+1) + '.' + nwOctets[3]+ '/' + nw[1])
		
		Topology.addLinks(device,intfList)  
		

		logToFile.info("	  Setting the interfaces UP")

		Topology.setInterfaceUp(device,RouterPid,intfList)
		TopoDet = {}
		TopoDet.update({'Interfaceslist' : intfList, 'Nwlist': nwList})

	return TopoDet
	


			


