'''python script for smart home hub'''
# -*- coding:utf-8 -*-

import base64
from ctypes.wintypes import BYTE
import requests
from base64 import urlsafe_b64decode as b64_decode
from base64 import urlsafe_b64encode as b64_encode
from sys import argv as sys_argv
from sys import exit as sys_exit

#init
#region init
#cheking start arguments
if len(sys_argv) == 3:
    #main module
    srv_url = sys_argv[1]
    hub_src = int(sys_argv[2], 16) #16 bit format

elif len(sys_argv) == 1:
    #only cheking timer
    srv_url = "http://localhost:9998"

else:
    print(99)
    sys_exit()
#endregion

#functions
#region functions
def bytes_to_uleb128(byte_arr:list) -> tuple:
    '''
    converting byte array to uleb128 value
    caution: only the first number will be converted
    return uleb128 value, number of bytes of this value
    '''
    result = 0
    shift = 0
    count_bytes = 0

    for byte in byte_arr:
        count_bytes += 1
        result |= (byte & 0x7F) << shift
        if byte & 0x80 == 0:
            break
        shift += 7
    
    return result, count_bytes

def get_data(arr:list) -> list:
    '''
    converting byte array to data list
    '''
    length = arr[0] #lenght of payload
    crc8 = arr[-1] 
    
    src, shift1 = bytes_to_uleb128(arr[1: -1])
    dst, shift2 = bytes_to_uleb128(arr[1 + shift1: -1])
    serial, shift3 = bytes_to_uleb128(arr[1 + shift1 + shift2: -1])
    print(src, dst, serial)

    shft = 1 + shift1 + shift2 + shift3
    del shift1, shift2, shift3
    print(f"shift = {shft}")

    dev_type = arr[shft]
    cmd = arr[shft + 1]
    shft += 2

    print(f"dev={dev_type}, cmd = {cmd}")

    if dev_type == 6:
        #timer
        cmd_body, shft_cmd_body = bytes_to_uleb128(arr[shft:])
        print(f"cmd_body = {cmd_body}")
    print(crc8)
    
    result = [length, src, dst, serial, dev_type, cmd, cmd_body, crc8]
    
    return  result

#endregion

# test vals 'DAH_fwEBAQVIVUIwMeE==' 'DbMG_38EBgb8l47KlTGf'

response = requests.post(srv_url) 

packet = b64_decode(response.text)

byte_packet = [byte for byte in packet]

data_packet = get_data(byte_packet)

print(response.text)
print(packet)
print(byte_packet)
print(data_packet)
