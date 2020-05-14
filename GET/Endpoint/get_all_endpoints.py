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
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#GLOBAL VARIABLES
tenant_names = []
tenant_classes = []
endpoints = []
bd_vrf = {}
l3out_names = []
l3outs = []
l3out_endpoints = []

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
    
######################### << GET L2 ENDPOINTS >> #################################
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
                             
######################### << GET L3 ENDPOINTS >> #################################
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
        
#WRITE ENDPOINT CLASSES TO XSLX FILE WITH PANDAS (L2)
list_tn = []
list_anp = []
list_vrf = []
list_bd = []
list_epg = []
list_pod = []
list_node = []
list_ipg = []
list_ip = []
list_mac = []
list_vlan = []
for x in range(len(endpoints)):
    list_tn.append(endpoints[x].tn)
    list_anp.append(endpoints[x].anp)
    list_vrf.append(endpoints[x].vrf)
    list_bd.append(endpoints[x].bd)
    list_epg.append(endpoints[x].epg)
    list_pod.append(endpoints[x].pod)
    list_node.append(endpoints[x].node)
    list_ipg.append(endpoints[x].ipg)
    list_ip.append(endpoints[x].ip)
    list_mac.append(endpoints[x].mac)
    list_vlan.append(endpoints[x].vlan)
    
# Create a Pandas Excel writer using XlsxWriter as the engine.
sheet_l2endpoints = pd.DataFrame({'Tenant':list_tn,'ANP':list_anp,'VRF':list_vrf,'BridgeDomain':list_bd,'EPG':list_epg,'Pod':list_pod,'Node':list_node,'IPG':list_ipg,'IP':list_ip,'MAC':list_mac,'VLAN':list_vlan})

#WRITE CLASS L3Endpoint TO XLSX  WITH PANDAS (L3)
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
sheet_l2endpoints.to_excel(writer, sheet_name='L2_Endpoint')
sheet_l3endpoints.to_excel(writer, sheet_name='L3_Endpoint')
# Close the Pandas Excel writer and output the Excel file.
writer.save()       

print("DONE!!")    
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        