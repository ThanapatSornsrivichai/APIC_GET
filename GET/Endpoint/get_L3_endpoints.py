#Created by Thanapat Sornsrivichai 
#Please refer to thanapat.s@ait.co.th for personal usage.
#Tested on APIC version 4.2(2f)
import json
import csv
from csv import writer
import os.path
import re
import requests 
import pandas as pd
from datetime import datetime

#GLOBAL VARIABLES
tenant_names = []
l3out_names = []
l3outs = []
l3out_endpoints = []

#CLASS FOR L3OUT (PATH,DOM,VRF)
class L3Out:
    def __init__(self,path,tenant,dom,vrf,l3out,encap):
        self.path = path
        self.tenant = tenant
        self.dom = dom
        self.vrf = vrf
        self.l3out = l3out
        self.encap = encap

#CLASS FOR L3OUT ENDPOINTS 
class L3Endpoint:
    def __init__(self,tenant,pod,node,dom,vrf,ip,mac,vlan,interface,l3out):
        self.tenant = tenant
        self.pod = pod
        self.node = node
        self.dom = dom
        self.vrf = vrf
        self.ip = ip
        self.mac = mac
        self.vlan = vlan
        self.interface = interface
        self.l3out = l3out

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
url = f"https://{apic_ip}/api/node/class/fvTenant.json"
r = requests.get(url,verify=False,cookies = cookies)
response = r.text
data_df = json.loads(response)
tncount = int(data_df["totalCount"])
for x in range(tncount):
    tenant_names.append(data_df["imdata"][x]["fvTenant"]["attributes"]["name"])


#LOOP IN TENANT FOR L3OUT RESPONSE
for x in range(len(tenant_names)):
    l3out_url = f"https://{apic_ip}/api/node/mo/uni/tn-{tenant_names[x]}.json?query-target=children&target-subtree-class=l3extOut"
    r = requests.get(l3out_url,verify=False,cookies = cookies) 
    response = r.text
    data_l3out = json.loads(response)
    #LOOP IN L3OUT FOR PATH,DOM,VRF
    for i in data_l3out["imdata"]:    
        l3out = i["l3extOut"]["attributes"]["name"]
        #print(l3out)
        l3encap_url = f"https://{apic_ip}/api/node/mo/uni/tn-{tenant_names[x]}/out-{l3out}.json?query-target=subtree&target-subtree-class=l3extRsPathL3OutAtt"
        l3encap_res = requests.get(l3encap_url,verify=False,cookies = cookies) 
        response_l3encap = l3encap_res.text
        data_l3encap = json.loads(response_l3encap)
        for j in data_l3encap["imdata"]:
            if j.get('l3extRsPathL3OutAtt') is not None:
                l3encap = j['l3extRsPathL3OutAtt']['attributes']['encap']
        att_l3out_url = f"https://{apic_ip}/api/node/mo/uni/tn-{tenant_names[x]}/out-{l3out}.json?query-target=subtree&target-subtree-class=l3extRsNodeL3OutAtt,l3extRsL3DomAtt,l3extRsEctx,l3extRsPathL3OutAtt"
        l3path_res = requests.get(att_l3out_url,verify=False,cookies = cookies) 
        response_l3path = l3path_res.text
        data_l3path = json.loads(response_l3path)
        #print(data_l3path)
        #LOOP IN IMDATA RESPONSE FOR PATH,DOM,VRF
        for j in data_l3path["imdata"]:
            if j.get('l3extRsEctx') is not None:
                l3vrf = j['l3extRsEctx']['attributes']['tnFvCtxName']
                print(l3vrf)          
            elif j.get('l3extRsL3DomAtt') is not None:
                dom_tmp = j['l3extRsL3DomAtt']['attributes']['tDn']
                l3dom = dom_tmp[10:]
                print(l3dom)
            elif j.get('l3extRsNodeL3OutAtt') is not None:
                l3path = j['l3extRsNodeL3OutAtt']['attributes']['tDn']
                print(l3path)
                #print(l3out)
                l3outs.append(L3Out(l3path,tenant_names[x],l3dom,l3vrf,l3out,l3encap))

#L3OUT ARP COLLECTING
for m in range(len(l3outs)):
    #print("yolo")
    l3arp_url = f"https://{apic_ip}/api/node/mo/{l3outs[m].path}/sys/arp/inst/dom-{l3outs[m].tenant}:{l3outs[m].vrf}.json?query-target=subtree&target-subtree-class=arpAdjEp"
    r = requests.get(l3arp_url,verify=False,cookies = cookies)
    response = r.text
    #print(response)
    data_df = json.loads(response)
    #GET POD, NODE, ENCAP
    path_tmp = l3arp_url
    pod_pattern = "topology/(.*?)/n"
    l3pod = re.search(pod_pattern, path_tmp).group(1)
    node_pattern = f"topology/{l3pod}/(.*?)/sys"
    l3node = re.search(node_pattern,path_tmp).group(1)
    #print(l3pod)
    #print(l3node)
    #LOOP IN IMDATA FOR IP, MAC, VLAN, INTERFACE
    for n in data_df['imdata']:
        l3ip = n['arpAdjEp']['attributes']['ip']
        #print(l3ip)
        l3mac = n['arpAdjEp']['attributes']['mac']
        #print(l3mac)
        l3vlan = n['arpAdjEp']['attributes']['ifId']
        #print(l3vlan)
        l3interface = n['arpAdjEp']['attributes']['physIfId']
        #print(l3interface)
        l3out_endpoints.append(L3Endpoint(l3outs[m].tenant,l3pod,l3node,l3outs[m].dom,l3outs[m].vrf,l3ip,l3mac,l3outs[m].encap,l3interface,l3outs[m].l3out))
      

#WRITE CLASS L3Endpoint TO XLSX FILE
list_tn = []
list_pod = []
list_vrf = []
list_node = []
list_l3out = []
list_dom = []
list_ip = []
list_mac = []
list_vlan = []
for x in range(len(l3out_endpoints)):
    list_tn.append(l3out_endpoints[x].tenant)
    list_pod.append(l3out_endpoints[x].pod)
    list_vrf.append(l3out_endpoints[x].vrf)
    list_node.append(l3out_endpoints[x].node)
    list_l3out.append(l3out_endpoints[x].l3out)
    list_dom.append(l3out_endpoints[x].dom)
    list_ip.append(l3out_endpoints[x].ip)
    list_mac.append(l3out_endpoints[x].mac)
    list_vlan.append(l3out_endpoints[x].vlan) 
    
now = datetime.now() 
# current date and time
date_time = now.strftime("%d%m%Y-%H%M")
# Create some Pandas dataframes from some data.
sheet_l3endpoints = pd.DataFrame({'Tenant':list_tn,'Pod':list_pod,'VRF':list_vrf,'Node':list_node,'L3Out':list_l3out,'Domain':list_dom,'IP':list_ip,'MAC':list_mac,'VLAN':list_vlan})
# Create a Pandas Excel writer using XlsxWriter as the engine.
writer = pd.ExcelWriter(f"BAAC_APIC_Endpoints_{date_time}.xlsx", engine='xlsxwriter')
# Write each dataframe to a different worksheet.
sheet_l3endpoints.to_excel(writer, sheet_name='L3_Endpoint')
# Close the Pandas Excel writer and output the Excel file.
writer.save()        

#WRITE CLASS L3Endpoint TO CVS FILE
csv_filename = "Endpoint_L3.csv"
file_exists = os.path.isfile(csv_filename)
fieldnames = ['Tenant','Pod','VRF','Node','L3Out','Domain','IP','MAC','VLAN']
with open(csv_filename,mode='w') as csv_file:
    csv_file = csv.DictWriter(csv_file,fieldnames = fieldnames,lineterminator = '\n')
    csv_file.writeheader()
    for x in range(len(l3out_endpoints)):
        csv_file.writerow({'Tenant':l3out_endpoints[x].tenant,'Pod':l3out_endpoints[x].pod,'VRF':l3out_endpoints[x].vrf,'Node':l3out_endpoints[x].node,'L3Out':l3out_endpoints[x].l3out,'Domain':l3out_endpoints[x].dom,'IP':l3out_endpoints[x].ip,'MAC':l3out_endpoints[x].mac,'VLAN':l3out_endpoints[x].vlan})  

print("DONE!")
        
    