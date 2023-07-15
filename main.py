'''python script for smart home hub'''
# -*- coding:utf-8 -*-

import base64
import requests
from base64 import urlsafe_b64decode as b64_decode
from base64 import urlsafe_b64encode as b64_encode
from sys import argv as sys_argv
from sys import exit as sys_exit

#region init
#cheking start arguments
if len(sys_argv) == 3:
    #main module
    address = sys_argv[1]
    inp_cmd = sys_argv[2]

elif len(sys_argv) == 1:
    #only cheking timer
    address = "http://localhost:9998"
    inp_cmd = " "
    
else:
    print(99)
    sys_exit()
#endregion

# test vals 'DAH_fwEBAQVIVUIwMeE==' 'DbMG_38EBgb8l47KlTGf'

dec_inp_cmd = b64_decode(inp_cmd)

response = requests.post(address, data=inp_cmd.encode('utf-8')) 

packet = [byte for byte in b64_decode(response.text) ]

print(packet)
