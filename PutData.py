import json

def putData(data,filename):
		
   	with open(filename,'w') as data_file:   
 		json.dump(data, data_file,indent = 4,sort_keys = True)
   	return



