import xml.etree.ElementTree as ET
import requests
from requests.auth import HTTPBasicAuth

username = 'apiuser'
password = 'JNn0Sg444s7D0jy5&'
BASE_URL = 'https://192.168.12.50/api/'

params = {
    'type': 'op',
    'cmd': '<show><system><info></info></system></show>'
}
resp = requests.get(
    BASE_URL,
    params=params,
    verify=False,
    timeout=5,
    auth=HTTPBasicAuth(username, password)
)
resp.raise_for_status()

root = ET.fromstring(resp.text)
output = root.find('result/system')