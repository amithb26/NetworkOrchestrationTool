*** Settings ***

Documentation     Resource file containing all the PYTHON API implementations.
Library           Setup.py
Library		  BGPSetup.py
Library           Collections

*** Keywords ***

Building Network Topology with specified number of devices 

	Log To Console    Building Network Topology	
	${TopoDet}=    Run Keyword and Continue On Failure     buildNetworkTopology   
	${interface_list}=    Get From Dictionary    ${TopoDet}    Interfaceslist
	Set Suite Variable    ${interface_list}    
   	${network_list}=    Get From Dictionary    ${TopoDet}    Nwlist
	Set Suite Variable    ${network_list}  

Booting up the devices

	Log To Console    Booting devices
	Run Keyword and Continue On Failure     bootUpDevices

	
Get IPaddress List that should be assigned to DUT interfaces for a given network

	Log To Console    Get IPaddress List that should be assigned to DUT interfaces for a given network   
	${intfaddress}=    Run Keyword and Continue On Failure     getIPaddressList    ${network_list}    ${interface_list}           	
	Set Suite Variable    ${intfaddress}   

Set Topology file with all device details

	Log To Console    Set Topology file that should be accessed to set configure devices  
	Run Keyword and Continue On Failure     setTopologyFile    ${interface_list}    ${intfaddress}          


Configure IPaddress on DUT 

	Log To Console    Configure IPaddress on DUT
	Run Keyword and Continue On Failure     configureIPaddress  

Run Ping test
	Log To Console    Running ping test 
	Run Keyword and Continue On Failure     pingTest   

Set all the required parameters for BGP configuration

	Log To Console    Setting BGP parameters
	Run Keyword and Continue On Failure     setBGPParameters

Set all the peer details and load it into json file
	
	Log To Console    Set BGP peer details 
	Run Keyword and Continue On Failure     setPeersDetails

Create BGP Neighbor for DUT

	Log To Console    creating BGPV4 neighbors
        Run Keyword and Continue On Failure     createBGPNeighbor    all

Check if BGP neighbors are set

	Log To Console    Checking if BGPV4 neighbors are set
	Run Keyword and Continue On Failure     checkBGPNeighbors    all
         

			
