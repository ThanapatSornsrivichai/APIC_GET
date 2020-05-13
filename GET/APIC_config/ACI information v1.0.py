import json
import csv
from csv import writer
import os.path
import re
import requests 
import urllib3
import pandas as pd
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#list BD
bd = []
list_bd_name = []
list_bd_vrf = []
list_bd_des = []
list_bd_tenant = []
list_bd_gateway_ip =[]
list_bd_mac = []
list_bd_subnet_type = []
#CLASS FOR BD
class BD:
    def __init__(self,tn,vrf,name,des,mac,ip,subnet_type):   
        self.tn = tn
        self.vrf = vrf
        self.name = name
        self.des = des
        self.mac = mac
        self.ip = ip
        self.subnet_type = subnet_type

#open file 
with open('ce2_DailyBackupToServer-2020-05-07T00-00-27_1.json') as json_file:
      data = json.load(json_file)
      count = int(len(data["polUni"]["children"]))
      #BD
      for x in range(count):
          bd_name = ''
          bd_des = ''
          bd_tenant = ''
          bd_mac = ''
          bd_gateway_ip = ''
          bd_vrf = ''
          bd_subnet_type = ''
          if data["polUni"]["children"][x].get('fvTenant') is not None:
              fvtenant_count = int(len(data["polUni"]["children"][x]["fvTenant"]["children"]))
              
              for y in data["polUni"]["children"][x]["fvTenant"]["children"]:
                  if y.get('fvBD') is not None:
                      print( y["fvBD"]["attributes"]["name"])
              # bd_tenant = data["polUni"]["children"][x]["fvTenant"]["attributes"]["name"]
              # for y in range(fvtenant_count):
              #     if data["polUni"]["children"][x]["fvTenant"]["children"][y].get('fvBD') is not None:
              #         bd_name = data["polUni"]["children"][x]["fvTenant"]["children"][y]["fvBD"]["attributes"]["name"]
              #         bd_des = data["polUni"]["children"][x]["fvTenant"]["children"][y]["fvBD"]["attributes"]["descr"]
              #         bd_mac = data["polUni"]["children"][x]["fvTenant"]["children"][y]["fvBD"]["attributes"]["mac"]
                     
              #         if data["polUni"]["children"][x]["fvTenant"]["children"][y]["fvBD"]["children"][0].get('fvSubnet') is not None:
              #             bd_gateway_ip = data["polUni"]["children"][x]["fvTenant"]["children"][y]["fvBD"]["children"][0]["fvSubnet"]["attributes"]["ip"]
              #             bd_vrf = data["polUni"]["children"][x]["fvTenant"]["children"][y]["fvBD"]["children"][3]["fvRsCtx"]["attributes"]["tnFvCtxName"]
              #             bd_subnet_type = data["polUni"]["children"][x]["fvTenant"]["children"][y]["fvBD"]["children"][0]["fvSubnet"]["attributes"]["scope"] 
              #         bd.append(BD(bd_tenant,bd_vrf,bd_name,bd_des,bd_mac,bd_gateway_ip,bd_subnet_type))
                      
for x in range(len(bd)):
    list_bd_name.append(bd[x].name)
    list_bd_vrf.append(bd[x].vrf)
    list_bd_des.append(bd[x].des)
    list_bd_tenant.append(bd[x].tn)
    list_bd_gateway_ip.append(bd[x].ip)
    list_bd_mac.append(bd[x].mac)
    list_bd_subnet_type.append(bd[x].subnet_type)

now = datetime.now() 
# current date and time
date_time = now.strftime("%d%m%Y-%H%M")
# Create some Pandas dataframes from some data.
sheet1 = pd.DataFrame({'Tenant': list_bd_tenant,'VRF': list_bd_vrf,'Description': list_bd_des,'bd_mac': list_bd_mac,'bd_gateway_ip': list_bd_gateway_ip,'subnet_type':list_bd_subnet_type})
# Create a Pandas Excel writer using XlsxWriter as the engine.
writer = pd.ExcelWriter(f"BD v1.5 {date_time}.xlsx", engine='xlsxwriter')
# Write each dataframe to a different worksheet.
sheet1.to_excel(writer, sheet_name='BD')
# Close the Pandas Excel writer and output the Excel file.
writer.save()        



          
     

