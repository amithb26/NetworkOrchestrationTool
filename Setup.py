import pexpect
from robot.output import librarylogger
from robot.running.context import EXECUTION_CONTEXTS

import time
import basicConfiguration
import logging
from loggerSetup import logToFile
from Buffer import flushBuffer
from GetData import getData
from Execute import executeCmd
from PutData import putData
from buildNetworkTopology import buildNetwork



#This class defines methods that implement the setup actions to be performed before configuration of any protocol
# 	Building Network Topology
# 	Booting up the devices
#	Configuring IP address
# 	Verifying IP address configuration by performing PING Test  



class Setup:

	def __init__(self):					#Initializes class object with below variables
						
		self.device = pexpect.spawn("/bin/bash")
		self.data = getData('variable.json')
		self.NumberOfDevices = self.data["NumberOfDevices"]
		self.Network = self.data["Network"]

		

	def buildNetworkTopology(self):				#Builds Network Topology i:e instantiate devices(docker containers),load containers with latest flexswitch image,addlinks and set interfaces UP 

		print "In build network"
		TopologyType = self.data['TopologyType']
		image = self.data["flexswitchImage"]
		logToFile.info('Building Network Topology')		
		TopologyDetails = buildNetwork(TopologyType,image)
		logToFile.info('	Network Topology of type %s is built with %d devices having %s as interfaces of devices and populated with %s networks' ,TopologyType,self.NumberOfDevices,TopologyDetails["Interfaceslist"],TopologyDetails["Nwlist"])
		return TopologyDetails


	def bootUpDevices(self):				#Boots all instantiated network devices
		
		logToFile.info("Booting up all the devices")
		basicConfiguration.boot(self.device)
		logToFile.info('All the %d network devices booted',self.NumberOfDevices)
		return


	def getIPaddressList(self,network_list,intflist):	#Gets the list of IP addresses from the pool of available IPs in a given network,that should be alloted to devices   			
		logToFile.info("Getting the IP address List")									
		IPaddressList = []
		for i in network_list:
			IPaddressList = basicConfiguration.getIPaddList(unicode(i),IPaddressList)
		logToFile.info('	  IP address list that can be allocated to %s interfaces is %s respectively',intflist,IPaddressList)
		return IPaddressList


	def setTopologyFile(self,intfList,IPaddressList):	#Adds all the topology reated details to a file called Topology.json
		
		logToFile.info("Setting up the topology file")
		Network = self.data["Network"]
		subnet = Network.split("/")
		DATA = {}
		DATA.update({"Device_details" : {}})

		for i in range(1,(self.NumberOfDevices+1)):
			Router = "Router"+str(i)
			DATA["Device_details"].update({Router : {}})
		j = 0 ; i = 2
		maxiter = len(intfList)

		while j != maxiter:
			if j % 2 == 0:
				DATA["Device_details"]["Router1"].update({intfList[j] : IPaddressList[j] + '/'+ subnet[1]})
				j = j + 1 
			else:
				Router = "Router" + str(i)
				DATA["Device_details"][Router].update({intfList[j] : IPaddressList[j] + '/' + subnet[1]})
				j = j + 1
				i = i + 1
		putData(DATA,'Topology.json')

		
		DATA.update({'Link_details' : {}})

		for i in range(1,(self.NumberOfDevices)):
			DATA['Link_details'].update({"Link_Router1_Router" + str(i+1) : {}})
		putData(DATA,'Topology.json')
		links = DATA["Link_details"].keys()
		links.sort()
		m = 0 ; n = 1
		
		for i in links:
			
			DATA['Link_details'][i].update({"Router1" : intfList[m],"Router"+str(n+1) : intfList[m+1]})
			m = m+2
			n = n+1
			
		putData(DATA,'Topology.json')	
		logToFile.info('	  Topology file is updated with below device details \n %s',DATA)
		return 


	def configureIPaddress(self):				#Configures IP address 
		
		data = getData('Topology.json')
		Devices = data['Device_details']
		Routers = Devices.keys()
		Routers.sort()
		for Router in Routers:
			logToFile.info('Configuring ip address on Device %s',Router)
			RouterInst = basicConfiguration.switchToRouter(self.device,Router)
 			RouterInst = basicConfiguration.preliminaryInstalls(RouterInst)
			#RouterInst = basicConfiguration.boot(RouterInst)
			interfaces = Devices[Router].keys()
			interfaces.sort()
			for intf in interfaces:
				interface = intf
				ipadd = Devices[Router][intf]
				RouterInst = basicConfiguration.configureIP(RouterInst,interface,ipadd)
				logToFile.info('	  IP address for %s interface of device %s is configured',interface,Router)
			RouterInst.sendline('exit')
			logToFile.info('IP address configured on all of the interfaces in %s',Router)
		return 


	def pingTest(self):					#Ping Test to verify IP address configuration

		topodata = getData('Topology.json')
		Routers = topodata['Device_details'].keys()
		Routers.sort()
		for Router in Routers:

			if Router == "Router1":
				RouterInst = basicConfiguration.switchToRouter(self.device,Router)
				for i in range(1,self.NumberOfDevices):
					NDUT = 'Router' + str(i+1)
					
					Link = "Link_Router1_"+ NDUT
					PeerInterface = topodata["Link_details"][Link][NDUT]
					IPAddress = topodata["Device_details"][NDUT][PeerInterface]
					basicConfiguration.ping(RouterInst,IPAddress)
			
			else:
				RouterInst = basicConfiguration.switchToRouter(self.device,Router)
				NDUT = 'Router1'
				Link = "Link_Router1_" + Router
				PeerInterface = topodata["Link_details"][Link][NDUT]
				IPAddress = topodata["Device_details"][NDUT][PeerInterface]
				basicConfiguration.ping(RouterInst,IPAddress)

		logToFile.info('Ping Test successful on all the devices') 
		return
					
					
			
			

		


obj = Setup()
topodet = obj.buildNetworkTopology()
obj.bootUpDevices()
network_list = topodet["Nwlist"]
intfList = topodet["Interfaceslist"]
IPaddressList = obj.getIPaddressList(network_list,intfList)	
obj.setTopologyFile(intfList,IPaddressList)
obj.configureIPaddress()
obj.pingTest()		

	                                
	

