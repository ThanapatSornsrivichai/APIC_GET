import requests 
import json
#https://172.26.99.201/api/node/mo/uni/tn-BAAC_TRANSIT.json?query-target=subtree&target-subtree-class=fvAEPg
#login
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
#GET ALL FALSE FROM ALL TENANT
for x in range(len(tenant_names)):
    url = f"https://{apic_ip}/api/node/mo/uni/tn-{tenant_names[x]}.json?query-target=subtree&target-subtree-class=fvAEPg&rsp-subtree-include=faults"
    r = requests.get(url,verify=False,cookies = cookies)
    response = response + r.text
    text_file = open(f"{tenant_names[x]}_false.txt","w")
    text_file.write(response)
    text_file.close()



