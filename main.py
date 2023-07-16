'''python script for smart home hub'''
# -*- coding:utf-8 -*-

import requests
from struct import pack as byte_pack
from base64 import urlsafe_b64decode as b64_decode
from base64 import urlsafe_b64encode as b64_encode
from sys import argv as sys_argv
from sys import exit as sys_exit

#constants
#region
broadcast = 0x3FFF
itself = 0x0000
high8bit = 0x80
low7bit = 0x7F
CRC_TABLE = [  0,  29,  58,  39, 116, 105,  78,  83, 232, 245, 210, 207, 156, 129, 166, 187, 
             205, 208, 247, 234, 185, 164, 131, 158,  37,  56,  31,   2,  81,  76, 107, 118, 
             135, 154, 189, 160, 243, 238, 201, 212, 111, 114,  85,  72,  27,   6,  33,  60, 
              74,  87, 112, 109,  62,  35,   4,  25, 162, 191, 152, 133, 214, 203, 236, 241, 
              19,  14,  41,  52, 103, 122,  93,  64, 251, 230, 193, 220, 143, 146, 181, 168, 
             222, 195, 228, 249, 170, 183, 144, 141,  54,  43,  12,  17,  66,  95, 120, 101, 
             148, 137, 174, 179, 224, 253, 218, 199, 124,  97,  70,  91,   8,  21,  50,  47, 
              89,  68,  99, 126,  45,  48,  23,  10, 177, 172, 139, 150, 197, 216, 255, 226, 
              38,  59,  28,   1,  82,  79, 104, 117, 206, 211, 244, 233, 186, 167, 128, 157, 
             235, 246, 209, 204, 159, 130, 165, 184,   3,  30,  57,  36, 119, 106,  77,  80, 
             161, 188, 155, 134, 213, 200, 239, 242,  73,  84, 115, 110,  61,  32,   7,  26, 
             108, 113,  86,  75,  24,   5,  34,  63, 132, 153, 190, 163, 240, 237, 202, 215, 
              53,  40,  15,  18,  65,  92, 123, 102, 221, 192, 231, 250, 169, 180, 147, 142, 
             248, 229, 194, 223, 140, 145, 182, 171,  16,  13,  42,  55, 100, 121,  94,  67, 
             178, 175, 136, 149, 198, 219, 252, 225,  90,  71,  96, 125,  46,  51,  20,   9, 
             127,  98,  69,  88,  11,  22,  49,  44, 151, 138, 173, 176, 227, 254, 217, 196
]
#endregion

def failure(value=99):
    '''Something went wrong'''
    print(value)
    sys_exit()

def calculate_table_crc8(number=256):
    '''calculate {number} crc8 values'''  
    generator = 0x1D
    CRC_TABLE = [0] * number
    
    for dividend in range(number):
        currByte = dividend
        
        for bit in range(8):
            if currByte & 0x80:
                currByte = (currByte << 1) ^ generator
            else:
                currByte <<= 1
        CRC_TABLE[dividend] = currByte & 0xFF

    return CRC_TABLE

#print(calculate_table_crc8())

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

def convert_to_bytes(arr:list) -> list:
    '''return byte array of the HUB payload (ULEB128)'''
    binary_data = bytes()
    for i in range(0, 3):
        while payload[i] >= 128:
            binary_data += byte_pack('B', (payload[i] & 0x7F) | 0x80)
            payload[i] >>= 7
        binary_data += byte_pack('B', payload[i])

    for i in range(3, 5):
        binary_data += byte_pack('B', payload[i])

    name_bytes = payload[-1].encode()
    binary_data += byte_pack('B', len(name_bytes))
    binary_data += name_bytes

    return binary_data

def get_crc8(bytes_)->int:
    #print(bytes_)
    crc = 0x00
    for byte in bytes_:
        #print(f"byte={byte}", end=" ")
        data = byte ^ crc
       # print(f"data = {data}")
        crc = CRC_TABLE[data]

    return crc

def get_response_data(byte_arr:list) -> list:
    '''
    converting byte array to data list
    '''
    result = []

    while len(byte_arr) > 0:
        length = byte_arr[0] #lenght of payload
        temp_result = [lenght]

        src, shift1 = bytes_to_uleb128(byte_arr[1: lenght])
        temp_result.append(src)

        dst, shift2 = bytes_to_uleb128(byte_arr[1 + shift1: lenght])
        temp_result.append(dst)

        serial, shift3 = bytes_to_uleb128(byte_arr[1 + shift1 + shift2: lenght])
        temp_result.append(serial)

        shft = 1 + shift1 + shift2 + shift3 #shift byte len + first 3 uleb value 
        del shift1, shift2, shift3

        dev_type = byte_arr[shft]
        temp_result.append(dev_type)

        cmd = byte_arr[shft + 1]
        shft += 2 #shifting before cmd_body
        temp_result.append(cmd)

        if dev_type == 1:
            #hub
            if cmd == 1 or cmd == 2:
                print("IM HUB!")
                shft_cmd_body = byte_arr[shft] + 1 #shifting cmd_body block
                dev_name = byte_arr[shft + 1: shft + shft_cmd_body].decode()
                temp_result.append(dev_name)
            else:
                failure()

        elif dev_type == 6:
            #timer
            if cmd == 2:
                shft_cmd_body = byte_arr[shft] + 1
                dev_name = byte_arr[shft + 1: shft + shft_cmd_body].decode()
                temp_result.append(dev_name)
            elif cmd == 6:
                time_stamp, shft_cmd_body = bytes_to_uleb128(byte_arr[shft:])
                temp_result.append(time_stamp)
            else:
                failure()
        else: 
            failure()
        
        crc8 = byte_arr[shft + shft_cmd_body]
        temp_result.append(crc8)

        result.append(temp_result)
        byte_arr = byte_arr[shft + shft_cmd_body + 1::]

    return result


#init HUB01
#region
if len(sys_argv) == 3:
    #main module
    srv_url = sys_argv[1]
    src = int(sys_argv[2], 16) #16 bit format

elif len(sys_argv) == 1:
    #only cheking timer
    srv_url = "http://localhost:9998"
    src = 1 
else:
    failure()

dst = broadcast
serial = 1
dev_type = 1
cmd = 1
cmd_body = "HUB01"

payload = [src, dst, serial, dev_type, cmd, cmd_body]
bin_payload = convert_to_bytes(payload)

lenght = len(bin_payload)
crc8 = get_crc8(bin_payload)

hub01 = bytes()
hub01 += byte_pack('B', lenght)
hub01 += bin_payload
hub01 += byte_pack('B', crc8)

hub01_packet = b64_encode(hub01)

#endregion

response = requests.post(srv_url) 
packet = b64_decode(response.text)
data_packet = get_response_data(packet)

print(f"response from serwer:\n{data_packet}")
print(response.text)

print("\n\ntesting:\n")
test_packet = b64_decode("DbMG_39ABgbsxo7KlTFh==")
print(f"response 'DbMG_39ABgbsxo7KlTFh' (timer 6)\n {get_response_data(test_packet)}")

# test vals 'DAH_fwEBAQVIVUIwMeE==' 'DbMG_38EBgb8l47KlTGf' 'DbMG_39ABgbsxo7KlTFh' 

packet = b64_decode("DAH_fwEBAQVIVUIwMeE==")
print(f"\npacket DAH_fwEBAQVIVUIwMeE (hub from github (1,1)")
print(get_response_data(packet))

print("\npacket hub01")
print(get_response_data(hub01))
