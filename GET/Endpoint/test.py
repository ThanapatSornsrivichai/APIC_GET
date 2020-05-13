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
    def __init__(self,tn,anp,epg):      
        self.tn = tn
        self.anp = anp
        self.epg = epg
        
#CLASS FOR ENDPOINT
class Endpoint:
    def __init__(self,tn,anp,epg,ip,mac,vlan,pod,node,ipg):   
        self.tn = tn
        self.anp = anp
        self.epg = epg
        self.ip = ip
        self.mac = mac
        self.vlan = vlan
        self.pod = pod
        self.node = node
        self.ipg = ipg    

#APIC LOGIN
apic_ip = "172.26.99.201" #Insert APIC
username = "thanapat" #Insert Username
password ="JamesJames9" #Insert Password
endpoint = "https://" + apic_ip + "/api/aaaLogin.json"
post_data = { "aaaUser" : { "attributes": {"name":username,"pwd":password } } } 

#GET APIC SESSION COOKIE
r = requests.Session()
r = requests.post(endpoint, json=post_data, verify=False)
response = r.text
json_data = json.loads(response)
token = json_data['imdata'][0]['aaaLogin']['attributes']['token']
cookies ={'APIC-Cookie': token}

#GET ALL TENANT NAME
url = "https://172.26.99.201/api/node/class/fvTenant.json"
r = requests.get(url,verify=False,cookies = cookies)
response = r.text
data_df = json.loads(response)
tncount = int(data_df["totalCount"])
for x in range(tncount):
    tenant_names.append(data_df["imdata"][x]["fvTenant"]["attributes"]["name"])
        
#LOOP TENANT
for x in range(tncount):
    bd_vrf_url = f"https://172.26.99.201/api/node/mo/uni/tn-{tenant_names[x]}.json?query-target=subtree&target-subtree-class=fvBD&rsp-subtree=children&rsp-subtree-class=fvRsCtx"
    r = requests.get(bd_vrf_url,verify=False,cookies = cookies)
    response = r.text
    data_df = json.loads(response)
    for m in range(len(data_df['imdata'])):
        bd_key = data_df['imdata'][m]['fvBD']['attributes']['name']
        for n in range(len(data_df['imdata'][m]['fvBD']['children'])):
            if data_df['imdata'][m]['fvBD']['children'][n].get('fvRsCtx') is not None:
                vrf_value = data_df['imdata'][m]['fvBD']['children'][n]['fvRsCtx']['attributes']['tnFvCtxName']
                bd_vrf[bd_key] = vrf_value
                #print(bd_vrf)
   # print (bd_vrf['BD_DR_MPB_MGT'])
    anp_url = f"https://172.26.99.201/api/node/mo/uni/tn-{tenant_names[x]}.json?query-target=children&target-subtree-class=fvAp&rsp-subtree=full&rsp-subtree-class=fvAEPg,"
    r = requests.get(anp_url,verify=False,cookies = cookies)
    response = r.text
    data_df = json.loads(response)
    #LOOP FOR ANP IN EACH TENANT
    for i in range(len(data_df['imdata'])):
        anp_name = data_df["imdata"][i]['fvAp']['attributes']['name']
        #IN CASE ANP DON'T HAVE EPG
        if data_df["imdata"][i]['fvAp'].get('children') is not None:   
            #LOOP FOR EPG IN EACH ANP
            for j in range(len(data_df["imdata"][i]['fvAp']['children'])):
                epg_name = data_df["imdata"][i]['fvAp']['children'][j]['fvAEPg']['attributes']['name']
                #print(data_df["imdata"][i]['fvAp']['children'][j]['fvAEPg']['children'])
                if data_df["imdata"][i]['fvAp']['children'][j]['fvAEPg'].get('children') is not None:
                    for b in range(len(data_df["imdata"][i]['fvAp']['children'][j]['fvAEPg']['children'])):
                        if data_df["imdata"][i]['fvAp']['children'][j]['fvAEPg']['children'][b].get('fvRsBd') is not None:
                            bd_search = data_df["imdata"][i]['fvAp']['children'][j]['fvAEPg']['children'][b]['fvRsBd']['attributes']['tnFvBDName']
                            vrf_search = bd_vrf[bd_search]
                            print(vrf_search)
                            
                            
                            