#Created by Thanapat Sornsrivichai 
#Please refer to thanapat.s@ait.co.th for personal usage.
#Tested on APIC version 4.2(2f)
import json
import csv
from csv import writer
import os.path
import re
import requests 

#GLOBAL VARIABLES
tenant_names = []
tenant_classes = []
endpoints = []
bd_vrf = {}

#CLASS FOR TENANT, ANP, EPG 
class Tenant:
    def __init__(self,tn,anp,epg,bd,vrf):      
        self.tn = tn
        self.anp = anp
        self.epg = epg
        self.bd = bd
        self.vrf = vrf
        
#CLASS FOR ENDPOINT
class Endpoint:
    def __init__(self,tn,anp,epg,ip,mac,vlan,pod,node,ipg,bd,vrf):   
        self.tn = tn
        self.anp = anp
        self.epg = epg
        self.ip = ip
        self.mac = mac
        self.vlan = vlan
        self.pod = pod
        self.node = node
        self.ipg = ipg    
        self.bd = bd
        self.vrf = vrf

#APIC LOGIN
apic_ip = "172.26.99.201" #Insert APIC
username = "thanapat" #Insert Username
password ="JamesJames9" #Insert Password
endpoint = f"https://{apic_ip}/api/aaaLogin.json"
post_data = { "aaaUser" : { "attributes": {"name":username,"pwd":password } } } 

#GET APIC SESSION COOKIE
r = requests.Session()
r = requests.post(endpoint, json=post_data, verify=False)
response = r.text
json_data = json.loads(response)
token = json_data['imdata'][0]['aaaLogin']['attributes']['token']
cookies ={'APIC-Cookie': token}

#GET ALL TENANT NAME
url = f"https://{apic_ip}/api/node/class/fvTenant.json"
r = requests.get(url,verify=False,cookies = cookies)
response = r.text
data_df = json.loads(response)
tncount = int(data_df["totalCount"])
for x in range(tncount):
    tenant_names.append(data_df["imdata"][x]["fvTenant"]["attributes"]["name"])
        
#LOOP TENANT
for x in range(tncount):
    bd_vrf_url = f"https://{apic_ip}/api/node/mo/uni/tn-{tenant_names[x]}.json?query-target=subtree&target-subtree-class=fvBD&rsp-subtree=children&rsp-subtree-class=fvRsCtx"
    r = requests.get(bd_vrf_url,verify=False,cookies = cookies)
    response = r.text
    data_df = json.loads(response)
    for m in data_df['imdata']:
        bd_key = m['fvBD']['attributes']['name']
        for n in m['fvBD']['children']:
            if n.get('fvRsCtx') is not None:
                vrf_value = n['fvRsCtx']['attributes']['tnFvCtxName']
                bd_vrf[bd_key] = vrf_value
    anp_url = f"https://{apic_ip}/api/node/mo/uni/tn-{tenant_names[x]}.json?query-target=children&target-subtree-class=fvAp&rsp-subtree=full&rsp-subtree-class=fvAEPg,"
    r = requests.get(anp_url,verify=False,cookies = cookies)
    response = r.text
    data_df = json.loads(response)
    #LOOP FOR ANP IN EACH TENANT
    for i in data_df['imdata']:
        anp_name = i['fvAp']['attributes']['name']
        #IN CASE ANP DON'T HAVE EPG
        if i['fvAp'].get('children') is not None:   
            #LOOP FOR EPG IN EACH ANP
            for j in i['fvAp']['children']:
                epg_name = j['fvAEPg']['attributes']['name']
                if j['fvAEPg'].get('children') is not None:
                    for b in j['fvAEPg']['children']:
                        if b.get('fvRsBd') is not None:
                            bd_search = b['fvRsBd']['attributes']['tnFvBDName']
                            vrf_search = bd_vrf[bd_search]
                            tenant_classes.append(Tenant(tenant_names[x],anp_name,epg_name,bd_search,vrf_search))
                
#LOOP FOR GETTING ENDPOINT
for k in range(len(tenant_classes)):
    url = f"https://{apic_ip}/api/node/mo/uni/tn-{tenant_classes[k].tn}/ap-{tenant_classes[k].anp}/epg-{tenant_classes[k].epg}.json?query-target=children&target-subtree-class=fvCEp&rsp-subtree=children&rsp-subtree-class=fvRsToVm,fvRsVm,fvRsHyper,fvRsCEpToPathEp,fvIp,fvPrimaryEncap"
    r = requests.get(url,verify=False,cookies = cookies)
    response = r.text
    data_df = json.loads(response)
    #LOOP FOR LIST IMDATA
    for x in data_df['imdata']:
        vlan_tmp = x['fvCEp']['attributes']['encap']
        mac_tmp = x['fvCEp']['attributes']['mac']
        max_len =len(x['fvCEp']['children'])
        #IN CASE THERE ARE NO ENDPOINT IN EPG
        for n in x['fvCEp']['children']:
            if n.get('fvRsCEpToPathEp') is not None:
                path_tmp = n['fvRsCEpToPathEp']['attributes']['tDn']
                pod_pattern = "topology/(.*?)/p"
                pod_tmp = re.search(pod_pattern, path_tmp).group(1)
                node_pattern = f"topology/{pod_tmp}/(.*?)/pathep"
                node_tmp = re.search(node_pattern,path_tmp).group(1)
                ipg_pattern = "pathep-\[(.*?)\]"
                ipg_tmp = re.search(ipg_pattern,path_tmp).group(1)
        #LOOP FOR IP ADDRESS AND CONTRUCT ENDPOINT CLASS
                for i in x['fvCEp']['children']:
                    if i.get('fvIp') is not None:
                        ip_tmp = i['fvIp']['attributes']['addr']
                        endpoints.append(Endpoint(tenant_classes[k].tn,tenant_classes[k].anp,tenant_classes[k].epg,ip_tmp,mac_tmp,vlan_tmp,pod_tmp,node_tmp,ipg_tmp,tenant_classes[k].bd,tenant_classes[k].vrf))
            else:
                path_tmp = "n/a"

#WRITE ENDPOINT CLASSES TO CVS FILE     
csv_filename = "Endpoint.csv"
file_exists = os.path.isfile(csv_filename)
fieldnames = ['Tenant','ANP','VRF','BridgeDomain','EPG','Pod','Node','IPG','IP','MAC','VLAN']
with open(csv_filename,mode='w') as csv_file:
    csv_file = csv.DictWriter(csv_file,fieldnames = fieldnames,lineterminator = '\n')
    csv_file.writeheader()
    for x in range(len(endpoints)):
        csv_file.writerow({'Tenant':endpoints[x].tn,'ANP':endpoints[x].anp,'VRF':endpoints[x].vrf,'BridgeDomain':endpoints[x].bd,'EPG':endpoints[x].epg,'Pod':endpoints[x].pod,'Node':endpoints[x].node,'IPG':endpoints[x].ipg,'IP':endpoints[x].ip,'MAC':endpoints[x].mac,'VLAN':endpoints[x].vlan})  

print ('DONE!!')   






