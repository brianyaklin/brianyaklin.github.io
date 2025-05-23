---
date:
  created: 2021-03-02
categories:
  - Programmability
tags:
  - Cisco
  - Python
---

# Initial Thoughts on Cisco NFVIS API

With multiple Cisco NFVIS software upgrades planned in the near future I thought I would explore the API to see how this might help speed up the process. My initial goals for exploring the API were to:

- Discovery which end-points can be used for hardware and software inventory reporting
- Determine how to update the IP receive ACL's
- Automate transfer and registration of the new NFVIS image files

<!-- more -->

!!! note
    Cisco Network Function Virtualization Infrastructure Software (NFVIS) is a Linux-based infrastructure software designed for the virtualization of network functions such as Cisco's ISRv, ASAv, vWAAS and NGFWv as well as third-party platforms. This allows an organization to service-chain network functions without the need of deploying extra hardware.

For those that aren't familiar with the upgrade procedure of a Cisco ENCS platform running the NFVIS software, it is quite different than your typical Cisco router or switch. And understandably so, these devices are much more like a server running a hypervisor. Upgrading involves first identifying the correct image to move to (which has compatibility with the Cisco and 3rd party image you are running), copying the new image file to the platform, registering the image file (essentially a series of healthchecks on the file), and finally initiating the upgrade with that image. There big issue with the NFVIS software is that there is no method to downgrade to a previous release once you have upgraded.

## Cisco NFVIS API Documentation

The first hurdle that I came across was when attempting to load [Cisco's API Reference](https://www.cisco.com/c/en/us/td/docs/routers/nfvis/user_guide/b-api-reference-for-cisco-enterprise-nfvis.html])through their regular site. For the past few weeks myself and others on my team have received a message when browsing to this link where it doesn't load the page and simply returns the text 'null' under the Book Table of Contents section. I have been able to get a few results on Google linking to direct chapters, but not the chapters I needed for NFVIS system API calls. I eventually stumbled across [Cisco Content Hub](https://content.cisco.com/platform_home.sjs?platform=Cisco%20Enterprise%20NFV%20Infrastructure%20Software&release=3.9.1). This was my first time playing around with this content site but I was able to find the information I needed.

## API Basics

The NFVIS REST API uses [HTTP Basic Authentication](https://developer.mozilla.org/en-US/docs/Web/HTTP/Authentication#basic_authentication_scheme) as its authentication scheme. This authentication scheme transmits the username and password as base64 encoded strings, which means that they are passed over the network as clear text. HTTPS/TLS should always be used with the management of any network device if you are using a web GUI or API calls, so as a result the Cisco ENCS and NVFIS software protects these credentials from being eavesdropped on. These credentials are included as a key/value pair in the HTTP Headers. Including [Basic Authentication in the Python Requests](https://requests.readthedocs.io/en/master/user/authentication/) module is quite simple (details will be shown in a section below).

When exchanging data with the NFVIS API you have two options for the format of which you would like to work with; JSON or XML. I prefer working with JSON as there is a [standard JSON Python library](https://docs.python.org/3/library/json.html) for working with it, but both formats can easily be converted into Python dictionaries. The [standard XML Python library](https://docs.python.org/3/library/xml.etree.elementtree.html) isn't very user friendly, but [xmltodict](https://pypi.org/project/xmltodict/) is a good open-source alternative. Whichever method you pick will require that you set the HTTP headers of Content-Type and Accept with the values in the table below.

| Data Format        | Content-Type and Accept Header Value |
| ------------------ | ------------------------------------ |
| XML                | application/vnd.yang.data+xml        |
| JSON               | application/vnd.yang.data+json       |
| JSON (alternative) | application/vnd.yang.collection+json |

Although the documentation generalizes and indicates to use the above content-types, I have found that in some circumstances the content-type and accept header needs to be set to `application/vnd.yang.collection+json`. My particular use-case was when querying for ENCS switch (not PNIC interfaces) [interface statistics](https://content.cisco.com/chapter.sjs?uri=%2Fsearchable%2Fchapter%2Fcontent%2Fen%2Fus%2Ftd%2Fdocs%2Frouters%2Fnfvis%2Fuser_guide%2Fb-api-reference-for-cisco-enterprise-nfvis%2Fb-api-reference-for-cisco-enterprise-nfvis_chapter_010101.html.xml&platform=Cisco%20Enterprise%20NFV%20Infrastructure%20Software&release=3.9.1). No where did it indicate in the documentation to use a YANG collection in the content-type/accept headers until you look at the example for the API end-point `/api/running/switch/interface/gigabitEthernet` to display the configuration of _all_ interfaces (versus a single interface). This really tripped me up in the past until I finally saw the change in header value.

Another thing to note is that you can specify a URL query parameter of `?deep` on GET requests for some API end-points that allow you to gather more detailed information. An example would be the API end-point for verifying a bridge configuration which is `/api/config/bridges?deep`.

Lets look at a quick example of how to specify these settings when making an API GET request.

```python
from urllib.parse import urljoin
import requests
from requests.auth import HTTPBasicAuth

BASE_URL = 'https://10.1.1.1'
PATH = '/api/operational/platform-detail'
url = urljoin(BASE_URL, PATH)
headers = {
    'Content-Type': 'application/vnd.yang.data+json',
    'Accept': 'application/vnd.yang.data+json',
}

username = 'myuser'
password = 'mypassword'

resp = requests.get(
    url,
    headers=headers,
    verify=False,
    timeout=20,
    auth=HTTPBasicAuth(username, password)
)

resp_data = resp.json()
```

The above example sets our base URL and path so that we can query the API to get the platform details of the NFVIS device. We set our HTTP headers content-type and accept so that we will receive a JSON result. We then initiate a query with the Requests package by providing our URL, headers, and an authentication scheme of Basic with the username and password. Finally, if the query was successful we convert the JSON response into a Python dictionary named resp_data so that we can parse the data.

## Hardware and Software Inventory

As with any software upgrade project you need to identify what software is currently running across your inventory. Although it appears that it might be possible to manage Cisco ENCS platforms with Cisco DNA Center, thats currently not an option with what I'm working with. As a result, I explored which API end-points might be possible to obtain this information and came across `/api/operational/platform-detail`. Based on the API query we made in the API Basics section above, lets look at the response data

The first and only key in the dictionary represents the platform info. I have printed from this key onwards instead of the full dictionary as the formatting is easier to view below.

```python
>>> from pprint import pprint
>>> pprint(resp_data['platform_info:platform-detail'])
{'hardware_info': {'BIOS-Version': 'ENCS54_2.6.071220181123',
                   'CIMC-Version': 'NA',
                   'CIMC_IP': 'NA',
                   'CPU_Information': 'Intel(R) Xeon(R) CPU D-1557 @ 1.50GHz '
                                      '12 cores',
                   'Compile_Time': 'Friday, October 19, 2018 [12:41:34 PDT]',
                   'Disk_Size': '200.0 GB',
                   'Entity-Desc': 'Enterprise Network Compute System',
                   'Entity-Name': 'ENCS',
                   'Manufacturer': 'Cisco Systems, Inc.',
                   'Memory_Information': '32741192 kB',
                   'PID': 'ENCS5412/K9',
                   'SN': 'FGL#########',
                   'UUID': 'aaabbbcccdddeeefff',
                   'Version': '3.9.2-FC4',
                   'hardware-version': 'M3'},
 'port_detail': [{'Name': 'GE0-0'}, {'Name': 'GE0-1'}, {'Name': 'MGMT'}],
 'software_packages': {'Kernel_Version': '3.10.0-693.11.1.1.el7.x86_64',
                       'LibVirt_Version': '3.2.0',
                       'OVS_Version': '2.5.2',
                       'QEMU_Version': '1.5.3'},
 'switch_detail': {'Name': 'NA', 'Ports': 8, 'Type': 'NA', 'UUID': 'NA'}}
```

Looking further into this structure we can see that a variety of information is available and helpful in building out both a hardware and software inventory if we were to scan all NFVIS platforms in the environment. Within the information above I'm mainly looking at the following fields:

- SN - The serial number of the chassis
- PID - The Product ID of the chassis
- Version - The NFVIS software version currently being used

Placing this information into a report (ex. CSV) can help you track a software upgrade project, as it is easy to programmatically query all of your NFVIS platforms on a regular basis to see what has and has not been upgraded yet.

## Updating IP Receive ACLs

To be able to upgrade the NFVIS software you need to be able to transfer the new image file to the device. This can be performed using the web GUI (which will automatically register the image) or through using SCP. SCP is a great choice for programmatically performing this option but it requires that the host you are sending the files from is included in an IP receive ACL on the NFVIS device and that the scpd protocol is permitted in that ACL. As an example, if our file server had IP address 10.4.4.40 the command we would use on the CLI of the NFVIS platform to allow this would be:

```
config t
   system settings ip-receive-acl 10.4.4.40/32 service [ ssh https icmp scpd snmp ] priority 10 action accept
```

The above command permits only our specific host IP to communicate with various services like SSH, HTTPS, ICMP, SCPD, and SNMP. You can add or remove services based on your deployment, but for this specific use-case we need SCPD. Additionally, the priority number of 10 was arbitrarily chosen by me but think of it as the ACL sequence number. The action can be either accept, reject or drop.

However, going through a large number of devices and configuring these receive ACL's would be difficult to manage and maintain and performing this programmatically would be far quicker. Unfortunately, what I'm about to show is that using the NFVIS API doesn't make this an easy task.

To perform this using the NFVIS API you need to use the [System Configuration API's](https://content.cisco.com/chapter.sjs?uri=%2Fsearchable%2Fchapter%2Fcontent%2Fen%2Fus%2Ftd%2Fdocs%2Frouters%2Fnfvis%2Fuser_guide%2Fb-api-reference-for-cisco-enterprise-nfvis%2Fb-api-reference-for-cisco-enterprise-nfvis_chapter_0110.html.xml&platform=Cisco%20Enterprise%20NFV%20Infrastructure%20Software&release=3.9.1#id_20198) but the documentation doesn't actually tell you how to specifically update the ip-receive-acl. In fact, it doesn't mention receive ACL's at all. It was only in diving through the [Ansible NFVIS Role](https://github.com/CiscoDevNet/ansible-nfvis) that I was able to understand this further. The particular API end-point that must be used is `/api/config/system/settings` with a PUT request which is used to both modify or replace an existing resource. As Cisco's [API Request Methods](https://content.cisco.com/chapter.sjs?uri=%2Fsearchable%2Fchapter%2Fcontent%2Fen%2Fus%2Ftd%2Fdocs%2Frouters%2Fnfvis%2Fuser_guide%2Fb-api-reference-for-cisco-enterprise-nfvis%2Fb-api-reference-for-cisco-enterprise-nfvis_chapter_00.html.xml&platform=Cisco%20Enterprise%20NFV%20Infrastructure%20Software&release=3.9.1) documentation indicates, the PUT operation must contain the complete representation of the mandatory attributes of the resource. This means you need to include the configuration for the hostname, default-gw, managment IP address and management IP netmask.

Exploring the response data by continuing with the Python code that was run in the API Basics section above, but now we will send a HTTP GET to the end-point `/api/config/system/settings`

```python
PATH = '/api/config/system/settings'
url = urljoin(BASE_URL, PATH)

resp = requests.get(
    url,
    headers=headers,
    verify=False,
    timeout=20,
    auth=HTTPBasicAuth(username, password)
)

resp_data = resp.json()
```

Now that we have our response data in a Python dictionary we can see what information in the below output that all of the mandatory fields are included (hostname, default-gw, managment IP address and netmask), but some additional details are also included (CIMC access, logging servers and levels and IP receive ACL details). What you can also see is that the IP receive ACL information **does not** include details like what we see in the CLI commands that would be used to configure this, namely the action, priority, and services. We are not able to get this information from the API.

```python
>>> pprint(resp_data)
{'system:settings': {'cimc-access': 'enable',
                     'default-gw': '10.1.1.1',
                     'hostname': 'ENCS-WAN1',
                     'ip-receive-acls': {'ip-receive-acl': [{'source': '0.0.0.0/0'},
                                                            {'source': '10.3.3.0/24'}]},
                     'logging': {'host': [{'host': '10.3.3.30'}],
                                 'severity': 'informational'},
                     'mgmt': {'ip': {'address': '10.1.1.2',
                                     'netmask': '255.255.255.0'}},
                     'wan': {'ip': {'address': '192.168.1.1',
                                    'netmask': '255.255.255.252'},
                             'vlan': 10}}}
```

So I want to be able to update the ip-receive-acls to include a new entry for 10.4.4.40/32. In the [Ansible NFVIS Role](https://github.com/CiscoDevNet/ansible-nfvis) I was able to see that to add an entry the existing ip-receive-acl list like shown below (taken from ansible-nfvis/library/nfvis_system.py in the Ansible role)

```python
    response = nfvis.request('/config/system/settings')
    ...

    payload = {'settings':response['system:settings']}
    if nfvis.params['trusted_source']:
        ip_receive_acl = []
        for network in nfvis.params['trusted_source']:
            ip_receive_acl.append({'source': network, 'action': 'accept', 'priority': 0, 'service': ['https', 'icmp', 'netconf', 'scpd', 'snmp', 'ssh']})
        if 'ip-receive-acls' in payload['settings'] and 'ip-receive-acl' in payload['settings']['ip-receive-acls']:
            if payload['settings']['ip-receive-acls']['ip-receive-acl'] != ip_receive_acl:
                nfvis.result['what_changed'].append('trusted_source')
                payload['settings']['ip-receive-acls'] = {'ip-receive-acl': ip_receive_acl}
        else:
            nfvis.result['what_changed'].append('trusted_source')
            payload['settings']['ip-receive-acls'] = {'ip-receive-acl': ip_receive_acl}
```

Essentially the Ansible Role takes what is currently configured and assigns it to the response variable. Then the new payload variable is created by copying all existing system settings from the response variable. This ensures that all mandatory fields as well as all other fields are still defined with what we will be sending back to the API. Finally, if an Ansible YAML variable of `trusted_source` was set, iterate through entries and append each as a configuration which includes the source, action, prioority and services that are predefined within the role above. Evenetually it updates the payload with the new and old `ip-receive-acls` entries. This seems like a TON of work to simply add a single entry. You have to add all previous entries, merge them with your new entries, etc.

I wanted to test out if the Ansible Role was complex for a specific reason or simply if the NFVIS API required it to be that way, so I tested out a few things myself. I have included comments to describe what I'm testing in the below output.

```python
import json

# A new dictionary representing a new IP receivel ACL entry I want to add
new_entry = {'settings': {'ip-receive-acls': {'ip-receive-acl': [{'priority': 10, 'action': 'accept', 'source': '10.4.4.40/32', 'service': ['https', 'icmp', 'scpd', 'snmp', 'ssh']}]}}}

# The API requires we send it data in JSON or XML. I chose JSON
# json.dumps() converts our Python dict into a JSON string
json_entry = json.dumps(new_entry)

# Now to HTTP PUT the data to the server
PATH = '/api/config/system/settings'
url = urljoin(BASE_URL, PATH)

resp = requests.put(
    url,
    headers=headers,
    verify=False,
    timeout=20,
    auth=HTTPBasicAuth(username, password),
    data=json_entry
)

# Looking at the response status code we got a 400 and an error:
>>> resp.status_code
400
>>> resp.json()
{'errors': {'error': [{'error-message': 'unknown element: settings in /system:system/system:settings/system:settings', 'error-urlpath': '/api/config/system/settings', 'error-tag': 'malformed-message'}]}}

# So we need to include mandatory fields, lets try this instead
new_entry = {'system:settings': {'wan': {'vlan': 10, 'ip': {'netmask': '255.255.255.252', 'address': '192.168.1.1'}}, 'default-gw': '10.1.1.1', 'hostname': 'ENCS-WAN1', 'cimc-access': 'enable', 'ip-receive-acls': {'ip-receive-acl': [{'priority': 0, 'action': 'accept', 'source': '0.0.0.0/0', 'service': ['https', 'icmp', 'snmp', 'ssh'{'priority': 10, 'action': 'accept', 'source': '10.4.4.40/32', 'service': ['https', 'icmp', 'scpd', 'snmp', 'ssh']}]}, 'mgmt': {'ip': {'netmask': '255.255.255.0', 'address': '10.1.1.2'}}, 'logging': {'host': [{'host': '10.3.3.30'}], 'severity': 'informational'}}}
json_entry = json.dumps(new_entry)
resp = requests.put(
    url,
    headers=headers,
    verify=False,
    timeout=20,
    auth=HTTPBasicAuth(username, password),
    data=json_entry
)
>>> resp.status_code
200
```

After sending the HTTP PUT when testing this out I actually received a timeout exception. Make sure you include the timeout=20 parameter in your Requests call. This is because the Cisco NFVIS platform needs to commit the change that you sent to it and this seems to take a long time.

The difficulty with the working solution above is:

1. You need to redefine the already existing ACL entry for 0.0.0.0/0, but you don't actually know how it was configured because you can't see that in the original HTTP GET request
2. If you forget to include all previous entries, they are actually removed from the configuration so you have the ability to cause an impact

The only way I can see this being effective is if you are doing something close to Infrastructure as Code (IAC) and have a template of what IP receivel ACL entries should already exist stored in version control. Then if you are simply adding a new entry to all devices you can update your IAC and pull from that template to be deployed to your device. Still though, there are the mandatory fields that need to be included in the HTTP PUT such as the hostname, default-gw and management IP and netmask.

## Closing Words

My experience so far with the NFVIS API for data gathering and reporting has been a positive one. I can't say the same about making configuration changes via the API though. I'm still exploring the API and trying to find a more reasonable way to make configuration changes, as well as automating the deployment of new image files using SCP and registering those images via the API. Once I have experimented with this further I'll post about it with my experience!
