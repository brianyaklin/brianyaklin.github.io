import xml.etree.ElementTree as ET
import requests

username = 'apiuser'
password = 'JNn0Sg444s7D0jy5'
BASE_URL = 'https://192.168.12.50/api/'
params = {
    'type': 'keygen',
}
headers = {
    'Content-Type': 'application/x-www-form-urlencoded',
}
data = {
    'user': username,
    'password': password,
}
resp = requests.post(
    BASE_URL,
    params=params,
    headers=headers,
    data=data,
    verify=False,
    timeout=5,
)
resp.raise_for_status()

root = ET.fromstring(resp.text)
key = root.find('result/key').text

params = {
    'type': 'op',
    'cmd': '<show><system><info></info></system></show>'
}
headers = {
    'X-PAN-KEY': key,
}
resp = requests.get(
    BASE_URL,
    params=params,
    headers=headers,
    verify=False,
    timeout=5,
)
resp.raise_for_status()

root = ET.fromstring(resp.text)
output = root.find('result/system')