import pexpect
import time
import ipaddress
import re
from robot.api import logger
from loggerSetup import logToFile 
from Buffer import flushBuffer
from GetData import getData
from Execute import executeCmd
from PutData import putData
import logging
from robot.output import librarylogger
from robot.running.context import EXECUTION_CONTEXTS



def getRouterIDList(): 	
											#Gets RouterId for each created node from the given routerID Network
	data = getData('variable.json')
	NumberOfDevices = data["NumberOfDevices"]
	RouterIDList = []
	for i in range(1,(NumberOfDevices+1)):
		ID = "%s.%s.%s.%s" %(i,i,i,i) 
		RouterIDList.append(ID)
	return RouterIDList


def getASNumList(AS):									#Gets the AS Num for each created node 

	ASNumList = []
	data = getData('variable.json')
	NumberOfDevices = data["NumberOfDevices"]
	BGPType = data["BGPType"]
	
	if BGPType == "IBGP":

		for i in range(0,NumberOfDevices):
			ASNumList.append(AS)
	

	else:
		ASNumList.append(AS)
		for i in range(1,NumberOfDevices):
			ASNumList.append(AS + 1)

	return ASNumList
		
		
def setPeerDetails(Router):								#Sets the Peer details into the ProtocolSpecific JSON File

	vardata = getData('variable.json')
	NumberOfDevices = vardata["NumberOfDevices"]
	start = 'Router1'
	data = getData('ProtocolSpecific.json')
	topodata = getData('Topology.json')
	data["BGP_Parameters"][Router].update({"PeerDetails" : {}})
	
	if Router == start:
		
		for i in range(1,NumberOfDevices):
			NDUT = 'Router' + str(i+1)
			Link = "Link_Router1_"+ NDUT
			PeerASNum = data["BGP_Parameters"][NDUT]["ASNum"]
			PeerInterface = topodata["Link_details"][Link][NDUT]
			PeerAddress = topodata["Device_details"][NDUT][PeerInterface]
			Peer = "Peer"+str(i)
			data["BGP_Parameters"][Router]['PeerDetails'].update({Peer : {"ASNum" : PeerASNum, "IP_Address" : PeerAddress, "Interface" : PeerInterface}})
		putData(data,'ProtocolSpecific.json')

	else:

		NDUT = 'Router1'
		Link = "Link_Router1_" + Router
		PeerInterface = topodata["Link_details"][Link][NDUT]
		PeerAddress = topodata["Device_details"][NDUT][PeerInterface]
		PeerASNum = data["BGP_Parameters"][Router]["ASNum"]
		data["BGP_Parameters"][Router]['PeerDetails'].update({"Peer1" : {"ASNum" : PeerASNum, "IP_Address" : PeerAddress, "Interface" : PeerInterface}})
		putData(data,'ProtocolSpecific.json')
	return data


def switchToRouter(device,Router):							#Logins to specific Router
		
	flushBuffer(1,device)
	device.sendcontrol('m')
	device.expect(['/w+@.*/#',pexpect.EOF,pexpect.TIMEOUT],timeout=3)
	cmd = """sudo docker exec -it %s bash""" %(Router)
	device.sendline(cmd)
	device.expect(['/w+@.*/#',pexpect.EOF,pexpect.TIMEOUT],timeout=3)
	logger.info(device.before,also_console=True)
	output = device.before
	search = "Errorresponse from daemon: %s" %(Router)
	if re.search(search,output):
		raise RuntimeError(search)
	return device


	
def BGPglobal(RouterInst,AS_Num,RouterId):						#Performs Global BGP configuration

	var = 'BGPglobal'
	flushBuffer(1,RouterInst)
	RouterInst.expect(['/w+@.*/#',pexpect.EOF,pexpect.TIMEOUT],timeout=3)
	config = """curl -X PATCH "Content-Type: application/json" -d '{"ASNum":"%s","RouterId":"%s"}' http://localhost:8080/public/v1/config/BGPGlobal""" % (AS_Num, RouterId)
	RouterInst = executeCmd(RouterInst,config)
	RouterInst.expect(['/w+@.*/#',pexpect.EOF,pexpect.TIMEOUT],timeout=3)
	logger.info(RouterInst.before,also_console=True)
	output = RouterInst.before	
	outputCheck(RouterInst,var,output)
	return RouterInst

											#Creates BGP Neighbors
def createBGPV4Neighbor(RouterInst,PeerAS,NeighborAddress,Interface,BfdEnable=False,PeerGroup='',MultiHopTTL=0,LocalAS='',KeepaliveTime=0,AddPathsRx=False,UpdateSource='',RouteReflectorClient=False,MaxPrefixesRestartTimer=0,Description='',MultiHopEnable=False,AuthPassword='',RouteReflectorClusterId=0,AdjRIBOutFilter='',MaxPrefixesDisconnect=False,AddPathsMaxTx=0,AdjRIBInFilter='',MaxPrefixes=0,MaxPrefixesThresholdPct=80,BfdSessionParam='default',NextHopSelf=False,Disabled=False,HoldTime=0,ConnectRetryTime=0):
	
	var = 'createBGPV4Neighbor'
	flushBuffer(1,RouterInst)
	RouterInst.expect(['/w+@.*/#',pexpect.EOF,pexpect.TIMEOUT],timeout=3)
	config = """curl -X POST --header 'Content-Type: application/json' --header 'Accept: application/json' -d '{"PeerAS":"%s", "NeighborAddress":"%s","IntfRef":"%s", "IfIndex":0,"RouteReflectorClusterId":0, "MultiHopTTL":0,"ConnectRetryTime":60,"HoldTime":180,"KeepaliveTime":60,"AddPathsMaxTx":0}' 'http://localhost:8080/public/v1/config/BGPv4Neighbor'""" %(PeerAS,NeighborAddress,Interface)
	RouterInst = executeCmd(RouterInst,config)
	RouterInst.expect(['/w+@.*/#',pexpect.EOF,pexpect.TIMEOUT],timeout=3)
	logger.info(RouterInst.before,also_console=True)
	output = RouterInst.before
	outputCheck(RouterInst,var,output)
	return RouterInst

											#Check all bgp neighbors for the given router by viewing neighbor table

def checkAllBGPNeighbors(RouterInst):

	var = 'checkAllBGPNeighbors'
	flushBuffer(1,RouterInst)
	RouterInst.expect(['/w+@.*/#',pexpect.EOF,pexpect.TIMEOUT],timeout=3)
	config = """curl -H "Accept: application/json" "http://localhost:8080/public/v1/state/BGPv4Neighbors" | python -m json.tool"""
	RouterInst = executeCmd(RouterInst,config)
	RouterInst.expect(['/w+@.*/#',pexpect.EOF,pexpect.TIMEOUT],timeout=3)
	logger.info(RouterInst.before,also_console=True)
	output = RouterInst.before
	outputCheck(RouterInst,var,output)
	return RouterInst 

def checkIPV4Route(RouterInst):								#Check BGP Neighbors are learnt and populated in IPv4table 
	
	var = 'checkIPV4Route'
	flushBuffer(1,RouterInst)
	RouterInst.expect(['/w+@.*/#',pexpect.EOF,pexpect.TIMEOUT],timeout=3)
	config = """curl  -H "Accept: application/json" "http://localhost:8080/public/v1/state/IPv4Routes" | python -m json.tool"""
	RouterInst = executeCmd(RouterInst,config)
	RouterInst.expect(['/w+@.*/#',pexpect.EOF,pexpect.TIMEOUT],timeout=3)
	logger.info(RouterInst.before)
	output = RouterInst.before
	outputCheck(RouterInst,var,output)
	return RouterInst 



def checkBGPRoute(RouterInst):

	var = 'checkBGPRoute'
	flushBuffer(1,RouterInst)
	RouterInst.expect(['/w+@.*/#',pexpect.EOF,pexpect.TIMEOUT],timeout=3)
	config = """curl -i -H "Content-Type: application/json" "http://localhost:8080/public/v1/state/BGPv4Routes"""
	RouterInst = executeCmd(RouterInst,config)
	RouterInst.expect(['/w+@.*/#',pexpect.EOF,pexpect.TIMEOUT],timeout=3)
	logger.info(RouterInst.before,also_console=True)
	output = RouterInst.before
	outputCheck(RouterInst,var,output)
	return RouterInst 


def outputCheck(RouterInst,var,output):							#Interprets output
	
	
	if var == 'BGPglobal':
			
		if re.search('\"Result\"\:\"Success\"',output): 
			logToFile.info("Global BGP Configuration Done")

		elif re.search('\"Result\"\:\"Error\: Nothing to be updated\.\"',output):
			logToFile.info("Global BGP already configured")


	elif var == 'createBGPV4Neighbor':
			
		if re.search('\"Result\"\:\"Success\"',output): 
			logToFile.info("BGP Neighbor configuration done")

		elif re.search('\"Result\"\:\"Error\: Nothing to be updated\.\"',output):
			logToFile.info("BGP Neighbor already configured")


	elif var == 'checkAllBGPNeighbors':
		
		if re.search('\"ObjectId\":\s[\d|\w|\-|\"]+',output):
			logToFile.info("Verification-BGP Neighbors----PASS")

		else:
			logToFile.info("BGP Neighbors not configured properly")



	elif var == 'checkIPV4Route':
		
		if re.search('\"ObjectId\":\s[\d|\w|\-|\"]+',output):
			logToFile.info("Verification-BGP Neighbors : Checking IPV4 route----PASS")

		else:
			logToFile.info("BGP Neighbors not configured properly")

	
	elif var == 'checkBGPRoute':
		
		if re.search('\"ObjectId\":\s[\d|\w|\-|\"]+',output):
			logToFile.info("Verification-BGP Neighbors : Checking BGP route table----PASS")

		else:
			logToFile.info("BGP Neighbors not configured properly")









	
 
