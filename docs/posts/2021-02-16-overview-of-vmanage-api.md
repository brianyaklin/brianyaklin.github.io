---
date:
  created: 2021-02-16
tags:
  - Cisco
  - Viptela
  - SD-WAN
  - Python
---

# Overview of the Viptela vManage API

The move away from decentralized management of network devices has been a huge time saver when it comes to gathering data on these technologies. Although there is no single centralized manager or controller which manages all networking technologies, instead of querying each individual network device you have centralized managers for particular networking functions. Cisco DNAC for your wireless and switch infrastructure, Panorama, Cisco FirePower Management Center (FMC) or FortiManager for your firewall infrastructure, and in the case of this article Viptela's vManage for your SD-WAN overlay. While no centralized manager will be perfect, for many common bulk tasks it will save you quite a bit of time because of the API's that they expose to their administrators.

<!-- more -->

I want to provide an overview of the Viptela vManage API and my experiences with it over the past year. While I have not had the chance to use the API for performing configuration and on-boarding activities, the experience I have gained includes using the API for data gathering, reporting, and [automated health checks](2021-02-10-role-of-automated-health-checks.md). In this article I will cover:

- What is Viptela vManage?
- Exploring the API
- How to authenticate with the API using Python
- How to query an API end-point using Python
- A few nuances I have found with the API

This guide will not be providing an overview of Cisco's Viptela solution and all of the various components. Instead I will be focusing mostly on how to programmatically interact with the Viptela vManage controller.

## What is Viptela vManage?

For those that are unaware of Cisco's Viptela SD-WAN offering, a Viptela vManage is one of the three controller types; vManage, vBond and vSmart. While vBond and vSmart control how a Viptela vEdge router authenticates with the SD-WAN overlay and receives routing information, the vManage controller is the single pane-of-glass management platform where you can configure, maintain and monitor all aspects of the SD-WAN overlay network. Most organizations will only have a single vManage controller as it is capable of managing up to 2000 devices, but larger organizations will have a cluster of vManage controllers. The vManage controller is accessed primarily through a web GUI or via a REST API.

The vManage controller allows you to perform most basic troubleshooting without ever having to login to the vEdge routers directly. It exposes a dashboard showing WAN health across your entire overlay and allows you to view health information on individual vEdge device such as current CPU and memory utilization, hardware status, previous reboots and crashes, interface health and SD-WAN function health such as your TLOC, tunnel, and control connection health. There are detailed logs as well as in-depth application information of you have deep packet inspection (DPI) enabled.

What I do find lacking in the vManage web GUI is the fact that you are not able to get status information on several critical network protocols such as VRRP, OSPF and BGP. In fact vManage seemingly doesn't care about these protocols when it comes to reporting on the health of a vEdge, indicating that a device status is 'green' even if there is an issue with one of these layer 3 protocols. Instead, you must either login to a vEdge via SSH or use the vManage API to obtain status information on these protocols.

## Exploring the API

The Viptela vManage REST API exposes a large amount of information through dozens of API end-points. The [vManage REST API documentation](https://sdwan-docs.cisco.com/Product_Documentation/Command_Reference/Command_Reference/vManage_REST_APIs) provides details on each end-point, but I find one of the best ways to explore the API is live on your vManage directly by browsing to https://vmanage_ip:port/apidocs/ (entering your vManages IP address or hostname, and a port if not the default 443). The benefit of using the live API browser is that you are able to query the API and get live data from your own network, while the API provides details on what the different error codes are and what JSON properties are returned for each end-point.

The API provides end-points that allow you to:

- View detailed alarms, logs and events
- Obtain inventory information
- Analyze detailed statistical information
- Perform real-time monitoring and troubleshooting
- Perform configuration changes by associating templates and policies

You are able to perform typical CRUD (create, read, update, delete) functions agains the vManage API. The following example of an API end-point is one that provides you with an inventory of all vEdge devices associated with vManage:

> https://my-vmanage.company.com/dataservice/system/device/vedges

By sending an HTTP GET request to the above API end-point (or even browsing to it in your web browser) you will see a JSON object returned that represents the inventory of your vEdge's. I have shown an example below of the information that you can now programmatically parse and report on.

```javascript
"data": [
    {
      "deviceType": "vedge",
      "serialNumber": "aaabbbcccddd",
      "ncsDeviceName": "vedge-aaabbbcccddd",
      "configStatusMessage": "In Sync",
      "templateApplyLog": [
        "[8-Sep-2020 11:35:12 EDT] Configuring device with feature template: my_vEdge100B",
        "[8-Sep-2020 11:35:12 EDT] Generating configuration from template",
        "[8-Sep-2020 11:35:15 EDT] Checking and creating device in vManage",
        "[8-Sep-2020 11:35:18 EDT] Device is online",
        "[8-Sep-2020 11:35:18 EDT] Updating device configuration in vManage",
        "[8-Sep-2020 11:35:19 EDT] Pushing configuration to device.",
        "[8-Sep-2020 11:35:28 EDT] Pre-checks on vManage have passed. Continuing with pushing configuration to device.",
        "[8-Sep-2020 11:35:35 EDT] Pushing configuration to device. Please wait ... ",
        "[8-Sep-2020 11:37:15 EDT] Completed template push to device.",
        "[8-Sep-2020 11:37:16 EDT] Template successfully attached to device"
      ],
      "uuid": "aaabbbcccddd",
      "managementSystemIP": "0.0.0.0",
      "templateStatus": "Success",
      "chasisNumber": "aaabbbcccddd",
      "configStatusMessageDetails": "",
      "configOperationMode": "vmanage",
      "deviceModel": "vedge-100-B",
      "deviceState": "READY",
      "validity": "valid",
      "platformFamily": "vedge-mips",
      "vedgeCertificateState": "certinstalled",
      "rootCertHash": "f33793721bea88e0f718838bfa954588",
      "deviceIP": "192.168.25.104",
      "personality": "vedge",
      "uploadSource": "File Upload",
      "local-system-ip": "192.168.25.104",
      "system-ip": "192.168.25.104",
      "model_sku": "None",
      "site-id": "104",
      "host-name": "my_vEdge4",
      "version": "19.2.3",
      "vbond": "192.168.1.3",
      "vmanageConnectionState": "connected",
      "lastupdated": 1613484157308,
      "reachability": "reachable",
      "uptime-date": 1595364900000,
      "defaultVersion": "19.2.3",
      "availableVersions": [
        "19.2.2"
      ],
      "template": "my_vEdge100B",
      "templateId": "aa914bc6-d777-421e-a2a4-314693bc49c5",
      "lifeCycleRequired": false,
      "expirationDate": "NA",
      "hardwareCertSerialNumber": "NA"
    },
    ...
```

## Authenticating with the vManage API

Now that you have a high-level idea of the benefits the vManage API provides you lets look at an example of using Python to authenticate with the vManage API. Because information in vManage isn't publicly exposed, it requires that each query be authenticated. Cisco provides a great [Python example class](https://sdwan-docs.cisco.com/Product_Documentation/Command_Reference/Command_Reference/vManage_REST_APIs/vManage_REST_APIs_Overview/Using_the_vManage_REST_APIs#Establish_a_Session_to_the_vManage_Server) that can be used with the REST API for GET and POST calls and details below will follow that example in a simpler fashion.

!!! note
    There is no explicit configuration needed to enable the vManage API. Instead, you simply use the API end-point paths in the API documentation and authenticate with your regular administrator credentials. Access is granted based on the roles associated with your ID.

First start off by importing the Requests package and disabling certificate warnings (unless you already have a trusted certificate on your vManage). The [Requests](https://requests.readthedocs.io/en/master/user/quickstart/) package is a great utility for interfacing with HTTP based servers such as the vManage API.

```py
>>> import requests
>>> from requests.packages.urllib3.exceptions import InsecureRequestWarning
>>> requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
```

Lets now create a few variables that we will be using when interfacing with the API such as the base URL, authentication path, username and password. Replace the content of the variables below with the information for your environment. The authentication path that must be used with the vManage API is /j_security_check.

```py
>>> base_url = 'https://my-vmanage.company.com'
>>> auth_path = '/j_security_check'
>>> username = 'my_username'
>>> password = 'my_password'
```

Now we can create a Requests session that will authenticate us against the API. We do so by sending an HTTP POST request to the authentication path and providing our username and password in the request body as a JSON object with specific parameter keys named `j_username` and `j_password`. These are keys that the vManage API defines and requires. The verify parameter of the session POST allows me to ignore untrusted certificates in my lab, and specifying a timeout value is a best-practice when using the sending a request so that the Requests package doesn't sit there indefinitely.

```py
>>> req_url = base_url + auth_path
>>> req_data = {'j_username': username, 'j_password': password}
>>> sess = requests.session()
>>> resp = sess.post(url=req_url, data=req_data, verify=False, timeout=10)
```

So we have now established an HTTP session with our vManage and we can verify that we have successfully established this session based on the HTTP status code 200:

```py
>>> resp.status_code
200
```

However, if we close the existing session and establish a new session with incorrect credentials you will see that although we fail authentication an HTTP 200 (OK) is still returned. Normally you would expect an HTTP 401 status code (Unauthorized)

```py
>>> sess.close()
>>> req_data = {'j_username': 'mybadusername', 'j_password': 'mybadpassword'}
>>> sess = requests.session()
>>> resp = sess.post(url=req_url, data=req_data, verify=False, timeout=10)
>>> resp.status_code
200
```

What you will see is that if you fail to authenticate against the API the HTTP status code is still 200, but the content of the response is the authentication form on the /j_security_check page. The following is a trimmed down version of the response content but it shows an HTML paragraph tag indicating 'Invalid User or Password'

```py
>>> resp.content.decode('utf-8')
'<html>
...
<span>Cisco vManage</span></div>\n\t\t\t\t\t<p id="errorMessageBox" name="errorMessageBox" class=\'errorMessageBox \'>Invalid User or Password</p>
...
</html>'
```

So as Cisco's [example class](https://sdwan-docs.cisco.com/Product_Documentation/Command_Reference/Command_Reference/vManage_REST_APIs/vManage_REST_APIs_Overview/Using_the_vManage_REST_APIs#Establish_a_Session_to_the_vManage_Server)] indicates, if there is an <html> tag in the response content the login failed. A successful response returns a status code of 200 and no content

```py
>>> resp.status_code
200
>>> resp.content.decode('utf-8')
''
```

A quick method of validating if the login was successful would be a quick if statement searching for an HTML tag in the response content:

```py
import sys
if '<html>' in resp.content.decode('utf-8'):
    print('vManage login failed')
    sys.exit()
else:
    print('vManage login successful')
```

## Sending Queries to the vManage API

Now that we are successfully authenticated with the vManage API and a session established for sending requests across, lets explore sending requests and reading the response content. First lets set our request path to the inventory end-point I mentioned earlier in this article. We will then append this to the req_url variable

```py
>>> req_path = '/dataservice/system/device/vedges'
>>> req_url = base_url + req_path
>>> req_url
'https://my-vmanage.company.com/dataservice/system/device/vedges'
```

To query this end-point using the existing session we send an HTTP GET request and store the response and can also validate the response status code is 200 (OK)

```py
>>> resp = sess.get(url=req_url, verify=False, timeout=10)
>>> resp.status_code
200
```

The Requests package has a useful class function `.json()` that allows us to convert JSON response objects (which the vManage API sends us) to a Python dictionary. This dictionary has two keys named `header` and `data`

```py
>>> data = resp.json()
>>> data.keys()
dict_keys(['header', 'data'])
```

The nested `header` dictionary in your response object contains information that desribes the nested `data` dictionary. I don't often use the header dictionary other than to initially understand how the response data is transformed. If we look at the actual response data we see that it is a list of dictionaries, with each index in the list describing a vEdge router in the inventory that we queried. In our case we have four entries in this list and each entry has the keys as described below

```py
>>> type(data['data'])
<class 'list''>
>>> len(data['data'])
4
>>> data['data'][0].keys()
dict_keys(['deviceType', 'serialNumber', 'ncsDeviceName', 'configStatusMessage', 'templateApplyLog', 'uuid', 'managementSystemIP', 'templateStatus', 'chasisNumber', 'configStatusMessageDetails', 'configOperationMode', 'deviceModel', 'deviceState', 'validity', 'platformFamily', 'vedgeCertificateState', 'rootCertHash', 'deviceIP', 'personality', 'uploadSource', 'local-system-ip', 'system-ip', 'model_sku', 'site-id', 'host-name', 'version', 'vbond', 'vmanageConnectionState', 'lastupdated', 'reachability', 'uptime-date', 'defaultVersion', 'availableVersions', 'template', 'templateId', 'lifeCycleRequired', 'expirationDate', 'hardwareCertSerialNumber'])
```

As I have already briefly described this response data in the Exploring the API section above, I won't be going into further detail other than to say that this response data can be used to build an inventory report of your vEdge devices or to obtain basic status information as it relates to vManage's perspective.

I want to touch on synced data within the vManage API. The vManage controller contains a significant amount of information about the SD-WAN overlay and the vEdge devices within the vManage controller directly. API queries about this data are very fast because vManage doesn't need to contact a device to obtain additional data. However, when it comes to the real-time monitoring API's information may be out-of-data on vManage and the default option is that after you query the vManage API the controller actually needs to contact the end device for that data. Depending on the depth of information, queries that aren't synced with vManage can take a long time and you will need to adjust the Requests timeout value accordingly.

So, how do you tell if a query is synced with vManage? Within the API end-point path you should see a 'synced' flag. An example of a synced path is:

> https://vmanage-ip-address/dataservice/device/bfd/synced/sessions?deviceId=deviceId

The same path that is not synced, and therefore requires vManage to query the end device to obtain details is:

> https://vmanage-ip-address/dataservice/device/bfd/sessions?deviceId=deviceId

The above two paths query for BFD sessions from a particular vEdge device represented by the deviceId parameter (the system IP associated with a vEdge). Depending on your overlays policies, a device can have hundreds or thousands of BFD sessions. As a result, if you use the vManage synced path you will get a response far quicker than vManage having to query the vEdge router for the most up-to-date data. Often times the synced data will sufficient and only several minutes behind that of the action vEdge.

## vManage API Nuances

I have already highlighted one instance of an oddity with the vManage API when describing the authentication process and the fact that vManage doesn't return an HTTP 401 Unauthorized message if your authentication attempt was rejected. There are several other nuances that I have found when working with the vManage API.

It seems that consistent naming of response object property names across different API end-points, as well as spelling, was not a concern for Cisco. In the device inventory response object earlier in this post one of the property names was `chasisNumber`. Examples of inconsistent property names between end-points include those related to interface names. When checking for ARP table statistics, an entry associated with an interface uses the property name `if-name` while checking the status of an interface uses a property name of `ifname`. The same goes for the properties `ip` and `ip-address` associated with the ARP and interface status API end-points respectively. While these aren't a big deal overall, it does make things a little bit tricky when trying to initially write your code.

Some timestamp fields in responses report timestamps in Unix time down to the millisecond, others report it as a date/time with timezone info format. By using milliseconds in Unix time, you need to use a few tricks when converting this into a human readable timestamp. The following uses a timestamp from the `lastupdated` property in the device inventory API call we made earlier, which returned 1613484157308 as a value. As shown below, the default timestamp value will receive an error when converting this to a human readable format. After making the value less specific and converting from milliseconds to seconds you are able to easily use the datetime module to convert into a human readable timestamp. I'm sure there are more elegant ways around this.

```py
>>> from datetime import datetime
>>> ts = 1613484157308
>>> datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
ValueError: year 53099 is out of range
>>>
>>> ts = 1613484157308 / 1000
>>> datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
'2021-02-16 14:02:37'
```

Despite these few nuances, the API is very easy to work with and I have found it very useful on many occasions! I hope that you have found this post useful and I would appreciate any feedback that you might have. Feel free to reach out at the social media links above!
