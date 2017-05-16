import pexpect
import time
import BGPConfiguration
import re
from loggerSetup import logToFile
from Buffer import flushBuffer
from GetData import getData
from Execute import executeCmd
from PutData import putData
import logging
from robot.output import librarylogger
from robot.running.context import EXECUTION_CONTEXTS



#This class defines the methods that provide logic for implementing the BGP configuration
#	Setting up the Protocol Specific JSON file detailing BGP Parameters for each device in the network
#	Enabling BGP global
#	Creating BGP Neighbor
#	Check BGP Neighbors are learnt by viewing the Neighbor table, IPv4 table 


class BGPSetup:

	def __init__(self):						#Initializes class object with below variables

		self.device = pexpect.spawn("/bin/bash")
		self.data = getData('variable.json')
		self.NumberOfDevices = self.data["NumberOfDevices"]
		self.AS = self.data["AS"]
		


	def setBGPParameters(self):					#Adds prerequisite BGP related parameters of all the devices to a file caleed Protocol Specific JSON file 

		logToFile.info("	  Setting up the ProtocolSpecific.json file with BGP related Parameters")		
		DATA = {}
		DATA.update({'BGP_Parameters' : {}})
		RouterIDList = BGPConfiguration.getRouterIDList()
		ASNumList = BGPConfiguration.getASNumList(self.AS)
		for i in range(0,(self.NumberOfDevices)):
			Router = 'Router%d' %(i+1)
			DATA['BGP_Parameters'].update({Router :{'RouterID' : RouterIDList[i],'ASNum' : ASNumList[i]}})
		putData(DATA,'ProtocolSpecific.json')
		return

		
	def setPeersDetails(self):					#Determines the directly connected neighbors(peers) and update the related information about the peer to protocol specific JSON file  

		for i in range(0,(self.NumberOfDevices)):
			Router = 'Router%d' %(i+1)
			BGPdata = BGPConfiguration.setPeerDetails(Router)
		logToFile.info("		ProtocolSpecific.json file is updated with all the BGP parameters for all the devices")
		logToFile.info("		Protocol Specific JSON is as shown below \n   %s", BGPdata)
		return


	def enableBGPGlobal(self,Device):				#Enables BGP global
		
		logToFile.info("	  Enabling BGP Global")
		data = getData('ProtocolSpecific.json')
		RouterID = data['BGP_Parameters'][Device]['RouterID']
		AS = data['BGP_Parameters'][Device]['ASNum']
		RouterInst = BGPConfiguration.switchToRouter(self.device,Device)
		RouterInst = BGPConfiguration.BGPglobal(RouterInst,AS,RouterID)
		return RouterInst


	def createBGPNeighbor(self,Router):				#Creates BGP Neighbor

		data = getData('ProtocolSpecific.json')
		
		if (isinstance(Router,list)):

			for i in Router:
				logToFile.info("Configuring BGP in %s",i)
				RouterInst = self.enableBGPGlobal(i)
				Peers = data["BGP_Parameters"][i]['PeerDetails']
				logToFile.info("	  Setting up the neighbors")
				for peer in Peers.keys():
					PeerAS = data["BGP_Parameters"][i]['PeerDetails'][peer]['ASNum']
					PeerAddress = data["BGP_Parameters"][i]['PeerDetails'][peer]['IP_Address']
					PeerInterface = data["BGP_Parameters"][i]['PeerDetails'][peer]['Interface']
					RouterInst = BGPConfiguration.createBGPV4Neighbor(RouterInst,PeerAS,PeerAddress,PeerInterface)
					RouterInst.sendline('exit')
				logToFile.info("BGP configuration donein %s",i)

		elif Router == 'all':

			Routers = data['BGP_Parameters'].keys()
			Routers.sort()
			for Router in Routers:

				logToFile.info("Configuring BGP in %s",Router)
				self.device.expect(['/w+@.*/#',pexpect.EOF,pexpect.TIMEOUT],timeout=3)
				RouterInst = self.enableBGPGlobal(str(Router))
				Peers = data["BGP_Parameters"][str(Router)]['PeerDetails']
				logToFile.info("	  Setting up the neighbors")
				
				for peer in Peers.keys():
					
					PeerAS = str(data["BGP_Parameters"][str(Router)]['PeerDetails'][str(peer)]['ASNum'])
					PeerAddress = str(data["BGP_Parameters"][str(Router)]['PeerDetails'][str(peer)]['IP_Address'])
					PeerInterface = str(data["BGP_Parameters"][str(Router)]['PeerDetails'][str(peer)]['Interface'])
					NeighborAddress = PeerAddress.split('/')
					RouterInst = BGPConfiguration.createBGPV4Neighbor(RouterInst,PeerAS,NeighborAddress[0],PeerInterface)
				RouterInst.sendline('exit')
				logToFile.info("BGP configuration done in %s",Router)
		return


	def checkBGPNeighbors(self,Router):				#Check if BGP neighbors are learnt

		data = getData('ProtocolSpecific.json')

		if (isinstance(Router,list)):

			for i in Router:
				logToFile.info("Checking if BGP neighbors are set in %s",i)
				RouterInst = switchToRouter(self.device,i) 
				RouterInst = BGPConfiguration.checkAllBGPNeighbors(RouterInst)
				RouterInst = BGPConfiguration.checkIPV4Route(RouterInst)
				RouterInst.sendline('exit')
			logToFile.info("Verification of BGP Neighbors done in %s",i) 

		elif Router == 'all':

			for i in data['BGP_Parameters'].keys():

				logToFile.info("Checking if BGP neighbors are set in %s",i)
				RouterInst = BGPConfiguration.switchToRouter(self.device,i) 
				RouterInst = BGPConfiguration.checkAllBGPNeighbors(RouterInst)
				RouterInst = BGPConfiguration.checkIPV4Route(RouterInst)
				#RouterInst = BGPConfiguration.checkBGPRoute(RouterInst)
				RouterInst.sendline('exit')
			logToFile.info("Verification of BGP neighbors done in %s",i) 
		return 

	

	 	
		


obj = BGPSetup()
obj = BGPSetup()
obj.setBGPParameters()
obj.setPeersDetails()
obj.createBGPNeighbor('all')	
obj.checkBGPNeighbors('all')
		

			


