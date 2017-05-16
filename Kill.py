import pexpect
import time
import json
import os
from Buffer import flushBuffer
import re

def Kill():
	
	with open('variable.json') as data_file:    
 		data = json.load(data_file)
		
   	NumberOfDevices = data["NumberOfDevices"]
	device = pexpect.spawn("/bin/bash")
	
	for i in range(1,(NumberOfDevices+1)):
		flushBuffer(1,device)
		cmd = """sudo docker rm -f Router%d""" %(i)		
		device.sendline(cmd)
		device.expect(['/w+',pexpect.EOF,pexpect.TIMEOUT],timeout=1)
		print device.before


Kill()	

