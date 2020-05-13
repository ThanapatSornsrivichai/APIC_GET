import json
import csv
from csv import writer
import os.path
import re

#CLASS FOR ENDPOINT
class Endpoint:
    def __init__(self,ip,mac,vlan,pod,node,ipg):      
        self.ip = ip
        self.mac = mac
        self.vlan = vlan
        self.pod = pod
        self.node = node
        self.ipg = ipg

endpoints = []
data_df = json.load(open(r'C:\Users\Thanapat.S\.spyder-py3\Projects\Test\Explode\Endpoint\Client End-Points-Table-epg-EPG_TRANSIT_MDC2_BLD_PRD.json'))
#print(type(data_df['imdata'][1]['fvCEp']['children']))
#print(data_df['imdata'][1]['fvCEp']['children'][1])
for x in range(len(data_df['imdata'])):
    #LOOP FOR LIST IMDATA
    vlan_tmp = data_df['imdata'][x]['fvCEp']['attributes']['encap']
    mac_tmp = data_df['imdata'][x]['fvCEp']['attributes']['mac']
    max_len =len(data_df['imdata'][x]['fvCEp']['children']) 
    path_tmp = data_df['imdata'][x]['fvCEp']['children'][max_len-1]['fvRsCEpToPathEp']['attributes']['tDn']
    print(path_tmp)
    pod_pattern = "topology/(.*?)/p"
    pod_tmp = re.search(pod_pattern, path_tmp).group(1)
    node_pattern = f"topology/{pod_tmp}/(.*?)/pathep"
    node_tmp = re.search(node_pattern,path_tmp).group(1)
    ipg_pattern = "pathep-(.*?)\]"
    ipg_tmp = re.search(ipg_pattern,path_tmp).group(1)
    #print(len(data_df['imdata'][x]['fvCEp']['children']))
    for i in range(len(data_df['imdata'][x]['fvCEp']['children'])-1):
        #print(len(data_df['imdata'][x]['fvCEp']['children']))
        #print(f"children len ={i} ")
        #LOOP FOR CHILDREN IN fvCEp
        ip_tmp = data_df['imdata'][x]['fvCEp']['children'][i]['fvIp']['attributes']['addr']
        #print(data_df['imdata'][x]['fvCEp']['children'][i]['fvIp']['attributes'][''])
        endpoints.append(Endpoint(ip_tmp,mac_tmp,vlan_tmp,pod_tmp,node_tmp,ipg_tmp))
        
csv_filename = "Endpoint.csv"
file_exists = os.path.isfile(csv_filename)
fieldnames = ['Pod','Node','IPG','IP','MAC','VLAN']
with open(csv_filename,mode='w') as csv_file:
    csv_file = csv.DictWriter(csv_file,fieldnames = fieldnames,lineterminator = '\n')
    csv_file.writeheader()
    for x in range(len(endpoints)):
        csv_file.writerow({'Pod':endpoints[x].pod,'Node':endpoints[x].node,'IPG':endpoints[x].ipg,'IP':endpoints[x].ip,'MAC':endpoints[x].mac,'VLAN':endpoints[x].vlan})  
        #csv_file.writerow({'Port':ports[x].port,'Mode':ports.[x].mode,'AllowedVlan':ports.[x].allowedvlan,'AccessVlan':ports.[x].accessvlan,'Status':ports.[x].status,'Speed':ports.[x].speed})  
print("DONE!")
        






