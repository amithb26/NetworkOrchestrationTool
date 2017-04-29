import logging
from datetime import datetime 


logToFile = logging.getLogger('Robot')
fname = datetime.now().strftime('%Y%m%d%H%M%S') + 'Reportlog.txt'
hdlr = logging.FileHandler(filename = fname)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logToFile.addHandler(hdlr) 
logToFile.setLevel(logging.DEBUG)


   	
			
		
