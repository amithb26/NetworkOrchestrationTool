*** Settings ***
Documentation	        A test suite with tests to perform scalability test
Metadata 		Version          	 1.0
...	         	More Info         	 For more information about Robot Framework see http://robotframework.org
...               	Author            	 Payal Jain
...               	Date             	 1 April 2017  
...	                Executed At  	         ${HOST}
...		        Test Framework           Robot Framework Python

Resource          	Resource.robot

#Suite Setup       	setupActions 
            

*** Test Cases ***

setupActions

	Building Network Topology with specified number of devices 
	Booting up the devices
	Get IPaddress List that should be assigned to DUT interfaces for a given network
	Set Topology file with all device details
	Configure IPaddress on DUT 
	Run Ping test

BGP Setup
	
	Set all the required parameters for BGP configuration
	Set all the peer details and load it into json file
	Create BGP Neighbor for DUT


BGP Validation
        
	Check if BGP neighbors are set
	
