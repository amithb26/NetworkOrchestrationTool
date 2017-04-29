import pexpect
import time
from Buffer import flushBuffer



# This method will execute the single or set of curl commands to perform necessary configuration or to grab any data.
# At the same time it will also check the status of result.
# If pass, it continues with next operation to be performed and if error, resolves the error and continues with the execution

	
def executeCmd(child,cmds):
	flushBuffer(1,child)
	child.sendcontrol('m')
	child.sendline(cmds)
	return child


