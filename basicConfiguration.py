import pexpect
import time
import re
import ipaddress

from loggerSetup import logToFile
from Buffer import flushBuffer
from GetData import getData
from Execute import executeCmd
from PutData import putData
from robot.api import logger
import logging
from robot.output import librarylogger
from robot.running.context import EXECUTION_CONTEXTS

def boot(device):								#Boots network devices, Start the flexswitch services

	data = getData('variable.json')
	NumberOfDevices = data["NumberOfDevices"]
		
	for i in range(0,NumberOfDevices):
		Router = "Router"+str(i+1) 
		#RouterInst = switchToRouter(device,Router)
		device.expect(['/w+@.*/#',pexpect.EOF,pexpect.TIMEOUT],timeout=1)
		cmd = "sudo docker exec %s sh -c \"\/etc\/init\.d\/flexswitch restart\"" %(Router)	
		device.sendline(cmd)
		time.sleep(8)
		device.expect(['/w+@.*/#',pexpect.EOF,pexpect.TIMEOUT],timeout=1)
		logger.info(device.before,also_console=True)
	return

	

def getIPaddList(Network,IPaddressList):					#Gets the IPAddress for devices from pool of available IPs in the given network

	
	Hosts_IP = ipaddress.ip_network(Network,strict = False)
	count = 1
	for i in Hosts_IP.hosts():				
		if  count <= 2:
			IPaddressList.append(str(i))
			count = count + 1
		else:
			break
	return IPaddressList


def switchToRouter(device,Router):						#Logins to specific Router
		
	flushBuffer(1,device)
	device.sendcontrol('m')
	device.expect(['/w+@.*/#',pexpect.EOF,pexpect.TIMEOUT],timeout=2)
	cmd = """sudo docker exec -it %s bash""" %(Router)
	device.sendline(cmd)
	device.expect(['\d+',pexpect.EOF,pexpect.TIMEOUT],timeout=2)
	logger.info(device.before,also_console=True)
	output = device.before
	search = "Errorresponse from daemon: %s" %(Router)
	if re.search(search,output):
		raise RuntimeError(search)
			
	return device

	
def preliminaryInstalls(RouterInst):						#Performs preliminary installations such as curl_installation

	flushBuffer(1,RouterInst)
	RouterInst.sendcontrol('m')
	RouterInst.expect(['/w+@.*/#',pexpect.EOF,pexpect.TIMEOUT],timeout=2)
	RouterInst.sendline("sudo apt-get update")
	time.sleep(15)
	RouterInst.sendline("sudo apt-get install curl -y")
	time.sleep(50)
	RouterInst.expect(['/w+@.*/#',pexpect.EOF,pexpect.TIMEOUT],timeout=2)
	logger.info(RouterInst.before,also_console=True)
	return RouterInst		
				

def configureIP(RouterInst,Interface,IP_address):				#Configures IP address

	flushBuffer(1,RouterInst)
	RouterInst.sendcontrol('m')
	RouterInst.expect(['/w+@.*/#',pexpect.EOF,pexpect.TIMEOUT],timeout=2)
	config = """curl -H "Content-Type: application/json" -d '{"IpAddr": "%s", "IntfRef": "%s"}' http://localhost:8080/public/v1/config/IPv4Intf""" % (IP_address,Interface)
	RouterInst = executeCmd(RouterInst,config)
	outputCheck(RouterInst,Interface,IP_address,config)
	return RouterInst
	
		
def checkInterface(RouterInst,Interface,IPaddress):				#Checks if interfaces are UP

	flushBuffer(1,RouterInst)
	RouterInst.sendcontrol('m')
	RouterInst.sendline("ifconfig")
	RouterInst.expect(['/w+@.*/#',pexpect.EOF,pexpect.TIMEOUT],timeout=1)
	logger.info(RouterInst.before,also_console=True)
	output = RouterInst.before
	ip = "inet addr:%s" %(IPaddress)
	status = re.search(Interface,output)
	con = re.search(ip,output)
	if (status and con):
		return
	else:
		logToFile.info("Interface %s not UP",Interface)
		raise RuntimeError("Some error : Interface is not UP")
	

def restartSwitch(RouterInst):							#Restarts flexswitch, restarts its daemons

	RouterInst.expect(['/w+@.*/#',pexpect.EOF,pexpect.TIMEOUT],timeout=1)	
	RouterInst.sendline('service flexswitch restart')
	time.sleep(8)
	RouterInst.expect(['/w+@.*/#',pexpect.EOF,pexpect.TIMEOUT],timeout=1)
	logger.info(RouterInst.before,also_console=True)
	return


	
def outputCheck(RouterInst,Interface,IP_address,config):			#Interprets Output
	
	li = IP_address.split('/')
	count = 3
	RouterInst.expect(['/w+@.*/#',pexpect.EOF,pexpect.TIMEOUT],timeout=3)
	logger.info(RouterInst.before,also_console=True)
	output = RouterInst.before

	while count >= 0:

		if re.search('\"Result\"\:\"Success\"',output):
			checkInterface(RouterInst,Interface,li[0])
			break

		elif re.search('Failed to connect to localhost port 8080',output):

			logger.info("***        ERROR:Failed to connect to localhost port 8080               ***",also_console=True)
			logger.info( '***   Flexswitch not started properly : Please restart the flexswitch   ***',also_console=True)
			restartSwitch(RouterInst)
			RouterInst = executeCmd(RouterInst,config)
			RouterInst.expect(['/w+@.*/#',pexpect.EOF,pexpect.TIMEOUT],timeout=3)
			logger.info(RouterInst.before,also_console=True)
			output = RouterInst.before
			count = count - 1
			if count == -1:
				logToFile.debug("Error: Unable to start the flexswitch")
				raise RuntimeError("Some error : Unable to start the Flexswitch")
			else:
				continue


		elif re.search('System not ready',output):

			logger.info("***         ERROR:System not ready,Daemons still restarting		***",also_console=True)
			time.sleep(20)
			RouterInst = executeCmd(RouterInst,config)
			RouterInst.expect(['/w+@.*/#',pexpect.EOF,pexpect.TIMEOUT],timeout=3)
			logger.info(RouterInst.before,also_console=True)
			output = RouterInst.before
			count = count - 1
			if count == -1:
				logToFile.debug("Error: Unable to start the flexswitch")
				raise RuntimeError("Some error : Unable to start the Flexswitch")
			else:
				continue

		elif re.search("Invalid interface reference provided in ip intf config object", output):
			
			logToFile.debug("Invalid interface reference provided in ip intf config object")
			raise RuntimeError("Error : Interface reference provided, is incorrect(Check interface is up for that particular device)")

		elif re.search("ip address validation failed",output):

			logToFile.debug("ip address validation failed")
			raise RuntimeError("Error : IP address not specified correctly")

		elif re.search('\"Result\"\:\"Error\: Already configured\.',output):
			
			logToFile.info("IP address already configured")
			break

		elif re.search('curl : command not found',output):

			preliminaryInstalls(RouterInst)
			count = count -1
			if count == -1:
				logToFile.debug("Unable to install CURL : Check the internet connection")
				raise RuntimeError("Some error : Unable to install curl")
			else:
				continue
	return




def ping(RouterInst,IPAddress):							#Performs ping test to verify configuration of IP address on interfaces 

	IP = IPAddress.split('/')
	flushBuffer(1,RouterInst)
	RouterInst.sendcontrol('m')
	RouterInst.expect(['/w+@.*/#',pexpect.EOF,pexpect.TIMEOUT],timeout=3)
	cmd = "ping -c 3 %s" %(IP[0])
	RouterInst.sendline(cmd)
	RouterInst.sendcontrol('m')
	RouterInst.expect(['min/avg/max/mdev',pexpect.EOF,pexpect.TIMEOUT],timeout=3)
	output = RouterInst.before
	logger.info(RouterInst.before,also_console=True)
	
	if re.search("0% packet loss",output):
		logToFile.info("Ping Success: Device Reachable")
	else:
		logToFile.debug("Device Unreachable : Check IP address Configuration")
		raise RuntimeError("Error : Device Unreachable")

	return
	
	
		
