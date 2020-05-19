import json
import requests 
import pandas as pd
from datetime import datetime
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#GLOBAL VARIABLE
tenant_names = [] #LIST OF TENANT NAMES
faults = [] #LIST OF ALL FAULTS

#CLASS FOR TENANT FAULTS 
class Fault:
    def __init__(self,tenant,ack,affected,cause,code,created,descr,domain,lastTransition,severity):      
        self.tn = tenant
        self.ack = ack
        self.affected = affected
        self.cause = cause
        self.code = code
        self.created = created
        self.descr = descr
        self.domain = domain
        self.lt = lastTransition
        self.severity = severity   

#LOGIN

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
#GET ALL FALSE FROM ALL TENANT
#https://172.26.99.201/api/node/mo/uni/tn-BAAC_TRANSIT.json?rsp-subtree-include=faults,no-scoped,subtree
for x in range(len(tenant_names)):
    fault_url = f"https://{apic_ip}/api/node/mo/uni/tn-{tenant_names[x]}.json?rsp-subtree-include=faults,no-scoped,subtree"
    r = requests.get(fault_url,verify=False,cookies = cookies)
    response = r.text
    data_df = json.loads(response)
    for y in data_df['imdata']:
        if y.get('faultDelegate') is not None:
           ack = y['faultDelegate']['attributes']['ack']
           affected = y['faultDelegate']['attributes']['affected']
           cause = y['faultDelegate']['attributes']['cause']
           code = y['faultDelegate']['attributes']['code']
           created = y['faultDelegate']['attributes']['created']
           descr = y['faultDelegate']['attributes']['descr']
           domain = y['faultDelegate']['attributes']['domain']
           lastTransition = y['faultDelegate']['attributes']['lastTransition']
           severity = y['faultDelegate']['attributes']['severity']
           faults.append(Fault(tenant_names[x],ack,affected,cause,code,created,descr,domain,lastTransition,severity))
        elif y.get('faultInst') is not None:
            ack = y['faultInst']['attributes']['ack']
            affected = "N/A"
            cause = y['faultInst']['attributes']['cause']
            code = y['faultInst']['attributes']['code']
            created = y['faultInst']['attributes']['created']
            descr = y['faultInst']['attributes']['descr']
            domain = y['faultInst']['attributes']['domain']
            lastTransition = y['faultInst']['attributes']['lastTransition']
            severity = y['faultInst']['attributes']['severity']
            faults.append(Fault(tenant_names[x],ack,affected,cause,code,created,descr,domain,lastTransition,severity))
            

#WRITE CLASS L3Endpoint TO XLSX  WITH PANDAS (L3)
list_tn = []
list_ack = []
list_affected = []
list_cause = []
list_code = []
list_created = []
list_descr = []
list_domain = []
list_lt = []
list_severity = []

for x in range(len(faults)):
    list_tn.append(faults[x].tn)
    list_ack.append(faults[x].ack)
    list_affected.append(faults[x].affected)
    list_cause.append(faults[x].cause)
    list_code.append(faults[x].code)
    list_created.append(faults[x].created)
    list_descr.append(faults[x].descr)
    list_domain.append(faults[x].domain)
    list_lt.append(faults[x].lt)
    list_severity.append(faults[x].severity)
     
now = datetime.now() 
# current date and time
date_time = now.strftime("%d%m%Y-%H%M")
# Create some Pandas dataframes from some data.
sheet_tnfault = pd.DataFrame({'Tenant':list_tn,'ACK':list_ack,'Affected':list_affected,'Cause':list_cause,'Code':list_code,'Created':list_created,'Description':list_descr,'Domain':list_domain,'Last Transition':list_lt,'Severity':list_severity})
# Create a Pandas Excel writer using XlsxWriter as the engine.
writer = pd.ExcelWriter(f"BAAC_APIC_Faults_{date_time}.xlsx", engine='xlsxwriter')
# Write each dataframe to a different worksheet.
sheet_tnfault.to_excel(writer, sheet_name='Faults')
# Close the Pandas Excel writer and output the Excel file.
writer.save()     

print("DONE!!")


