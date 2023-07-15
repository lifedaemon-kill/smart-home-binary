'''python script for smart home hub'''
# -*- coding:utf-8 -*-

import requests
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
CRC_TABLE = [    0,   285,   570,   807,  1140,  1385,  1614,  1875,  2280,  2549,  2770,  3023, 
              3228,  3457,  3750,  4027,  4557,  4304,  5111,  4842,  5561,  5284,  6019,  5790, 
              6437,  6200,  6943,  6658,  7505,  7244,  8043,  7798,  9095,  8858,  8637,  8352, 
             10227,  9966,  9673,  9428, 11119, 10866, 10581, 10312, 12059, 11782, 11553, 11324, 
             12874, 13143, 12400, 12653, 13886, 14115, 13316, 13593, 15010, 15295, 14488, 14725, 
             16086, 16331, 15596, 15857, 18195, 17934, 17705, 17460, 17255, 17018, 16733, 16448, 
             20475, 20198, 19905, 19676, 19343, 19090, 18869, 18600, 22238, 22467, 21732, 22009, 
             21162, 21431, 20624, 20877, 24118, 24363, 23564, 23825, 23106, 23391, 22648, 22885, 
             25748, 25993, 26286, 26547, 24800, 25085, 25306, 25543, 27772, 28001, 28230, 28507, 
             26632, 26901, 27186, 27439, 30041, 29764, 30563, 30334, 28973, 28720, 29463, 29194, 
             32177, 31916, 32651, 32406, 31173, 30936, 31743, 31458, 36390, 36667, 35868, 36097, 
             35410, 35663, 34920, 35189, 34510, 34771, 34036, 34281, 33466, 33703, 32896, 33181, 
             40939, 40694, 40401, 40140, 39839, 39554, 39333, 39096, 38659, 38430, 38201, 37924, 
             37751, 37482, 37197, 36944, 44449, 44220, 44955, 44678, 43477, 43208, 44015, 43762, 
             42313, 42068, 42867, 42606, 41277, 40992, 41735, 41498, 48236, 48497, 48726, 48971, 
             47128, 47365, 47650, 47935, 46212, 46489, 46782, 47011, 45296, 45549, 45770, 46039, 
             51509, 51240, 51983, 51730, 52545, 52316, 53115, 52838, 49629, 49344, 50151, 49914, 
             50601, 50356, 51091, 50830, 55544, 55781, 56002, 56287, 56460, 56721, 57014, 57259, 
             53264, 53517, 53802, 54071, 54372, 54649, 54878, 55107, 60082, 60335, 59528, 59797, 
             61126, 61403, 60668, 60897, 57946, 58183, 57440, 57725, 58926, 59187, 58388, 58633, 
             64383, 64098, 63813, 63576, 65291, 65046, 64817, 64556, 62359, 62090, 61869, 61616, 
             63459, 63230, 62937, 62660]
#endregion

#functions
#region
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
            if (currByte & 0x80) != 0:
                currByte <<= 1
                currByte ^= generator
            else:
                currByte <<= 1
        CRC_TABLE[dividend] = currByte
    return CRC_TABLE

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
    result = []
    for value in arr[0:3]:
        while True:
            byte =  value & 0x7F
            value >>= 7
            if value == 0:
                result.append(byte)
                break
            else:
                result.append(byte | 0x80)

    result.extend(arr[3:5])
    result.append(bytes(arr[5], 'utf-8'))

def get_crc8(bytes_)->int:
    crc = 0
    for byte in bytes_:
        data = byte ^ crc
        crc = CRC_TABLE[data]
    
    return crc

def get_data(arr:list) -> list:
    '''
    converting byte array to data list
    '''
    length = arr[0] #lenght of payload
    
    src, shift1 = bytes_to_uleb128(arr[1: -1])
    dst, shift2 = bytes_to_uleb128(arr[1 + shift1: -1])
    serial, shift3 = bytes_to_uleb128(arr[1 + shift1 + shift2: -1])

    shft = 1 + shift1 + shift2 + shift3
    del shift1, shift2, shift3

    dev_type = arr[shft]
    cmd = arr[shft + 1]
    shft += 2
    
    if dev_type == 1:
        #hub
        if cmd == 1:
            #
            pass
        elif cmd == 2:
            pass
        else:
            failure()
    elif dev_type == 6:
        #timer
        pass
    else: 
        failure()

    cmd_body, shft_cmd_body = bytes_to_uleb128(arr[shft:])
        
    crc8 = arr[shft + shft_cmd_body]
    
    result = {'length':length, 
              'src':src, 
              'dst':dst, 
              'serial':serial, 
              'dev_type':dev_type, 
              'cmd':cmd, 
              'cmd_body':cmd_body, 
              'crc8':crc8
    }
    
    return  result

#endregion


#init
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
cmd_body = ["HUB01"]

payload = [src, dst, serial, dev_type, cmd, cmd_body]

bin_payload = convert_to_bytes(payload)
lenght = len(bin_payload)
crc8 = get_crc8(bin_payload)

hub01 = [lenght]
hub01.insert(bin_payload)
hub01.append(crc8)
#endregion

# test vals 'DAH_fwEBAQVIVUIwMeE==' 'DbMG_38EBgb8l47KlTGf'


response = requests.post(srv_url) 

packet = b64_decode(response.text)

byte_packet = [byte for byte in packet]

data_packet = get_data(byte_packet)

#print(response.text)
#print(packet)
#print(byte_packet)
packet = b64_decode("DAH_fwEBAQVIVUIwMeE==")
print(packet)
print([item for item in packet])
print(get_data([item for item in packet]))
