import requests 
import json
import csv
from csv import writer
import os.path
import re
#CLASS FOR PORT
class Port:
    def __init__(self, pod, node, port, mode, allowedvlan, accessvlan, status, speed):
        self.pod = pod        
        self.node = node
        self.port = port
        self.mode = mode
        self.allowedvlan = allowedvlan
        self.aceessvlan = accessvlan
        self.status = status
        self.speed = speed
        
ports = []
tenant_names = [] #LIST OF TENANT NAMES
apic_ip = "172.26.99.201" #Insert APIC
username = "thanapat" #Insert Username
password ="JamesJames9" #Insert Password
endpoint = "https://" + apic_ip + "/api/aaaLogin.json"
post_data = { "aaaUser" : { "attributes": {"name":username,"pwd":password } } } 

r = requests.Session()
r = requests.post(endpoint, json=post_data, verify=False)
response = r.text
json_data = json.loads(response)
token = json_data['imdata'][0]['aaaLogin']['attributes']['token']
cookies ={'APIC-Cookie': token}

#GET TENANT NAMES
url = f"https://{apic_ip}/api/node/class/fvTenant.json?rsp-subtree-include=health"
r = requests.get(url,verify=False,cookies = cookies)
response = r.text
data_df = json.loads(response)
totalCount = int(data_df["totalCount"])
for x in range(totalCount):
    tenant_names.append(data_df["imdata"][x]["fvTenant"]["attributes"]["name"])
print(tenant_names)

#GET PORT OPERATION STATE
pod_id = '1'
#node_ids = ['101','102','1101','1102','1103','1104','1105','1106','1201','1202','1203','1204','1205','1206','1301','1302','1303','1304','1305','1306','1401','1402','1403','1404']
node_ids = ['501','502','2501','2502','2503','2504','2505','2506','2507','2508','2509','2510']
for node_id in node_ids:
    url = f"https://{apic_ip}/api/node/mo/topology/pod-{pod_id}/node-{node_id}/.json?query-target=subtree&target-subtree-class=ethpmPhysIf"
    r = requests.get(url,verify=False,cookies = cookies)
    data_df = json.loads(r.text)
    
    for x in range(int(data_df["totalCount"])):
        path_tmp = data_df["imdata"][x]["ethpmPhysIf"]["attributes"]["dn"]
        pod_pattern = "topology/(.*?)/node"
        pod_tmp = re.search(pod_pattern, path_tmp).group(1)
        node_pattern = f"topology/{pod_tmp}/(.*?)/sys"
        node_tmp = re.search(node_pattern,path_tmp).group(1)
        port_pattern = "sys/phys-\[(.*?)\]/phys"
        port_tmp = re.search(port_pattern,path_tmp).group(1)
        #port_tmp = path_tmp
        #print(type(port_tmp))
        mode_tmp = data_df["imdata"][x]["ethpmPhysIf"]["attributes"]["operMode"]
        allowedvlan_tmp = " "+ data_df["imdata"][x]["ethpmPhysIf"]["attributes"]["allowedVlans"]
        accessvlan_tmp = " "+ data_df["imdata"][x]["ethpmPhysIf"]["attributes"]["accessVlan"]
        status_tmp = data_df["imdata"][x]["ethpmPhysIf"]["attributes"]["operSt"]
        speed_tmp = data_df["imdata"][x]["ethpmPhysIf"]["attributes"]["operSpeed"]
        ports.append(Port(pod_tmp,node_tmp,port_tmp,mode_tmp,allowedvlan_tmp,accessvlan_tmp,status_tmp,speed_tmp))
        
    #text_file = open(f"{node_id}_stat.txt","w")
    #text_file.write(r.text)
    #text_file.close()
csv_filename = "Ports.csv"
file_exists = os.path.isfile(csv_filename)
fieldnames = ['Pod','Node','Port','Mode','AllowedVlan','AccessVlan','Status','Speed']
with open(csv_filename,mode='w') as csv_file:
    #Tenant Name
    #print (data_df["polUni"]["children"][x+2]["fvTenant"]["attributes"]["name"]) 
    csv_file = csv.DictWriter(csv_file,fieldnames = fieldnames,lineterminator = '\n')
    csv_file.writeheader()
    for x in range(len(ports)):
        csv_file.writerow({'Pod':ports[x].pod,'Node':ports[x].node,'Port':ports[x].port,'Mode':ports[x].mode,'AllowedVlan':ports[x].allowedvlan,'AccessVlan':ports[x].aceessvlan,'Status':ports[x].status,'Speed':ports[x].speed})  
        #csv_file.writerow({'Port':ports[x].port,'Mode':ports.[x].mode,'AllowedVlan':ports.[x].allowedvlan,'AccessVlan':ports.[x].accessvlan,'Status':ports.[x].status,'Speed':ports.[x].speed})  
print("DONE!")






