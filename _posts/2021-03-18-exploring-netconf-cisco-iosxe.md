---
title: "Exploring NETCONF and YANG on Cisco IOS-XE"
tags:
  - Cisco
  - Python
  - Automation
---

I have been reading up on model-driven programmability using NETCONF and YANG models and found myself playing around with these after a [Reddit user](https://www.reddit.com/r/Cisco/comments/m7kmbe/how_to_add_the_yang_model_to_the_xml_file_for/) was having difficulty updating a Cisco IOS-XE interface description and VLAN. Other than reading about YANG and getting the basic capabilities from my lab router, I hadn't actually configured anything using NETCONF and YANG models before so this seemed like a good challenge to get me thinking in the right mindset. I suspected that it had to do with the XML namespace the user was referencing, but I had to figure out a way to prove it. In this post I will cover a little bit about NETCONF/YANG as well as how you can explore using it with your Cisco devices. This guide isn't meant to be a complete overview of these protocols, just something to get you started on learning about them.

## What is NETCONF?
Traditionally, network devices have been configured using their CLI's or through SNMP. While CLI's are great for one-off configurations, they are proprietary to each vendor, and configuring network devices this way doesn't scale well. SNMP can be used to configure portions of a network devices configuration, but it too doesn't scale well and lacks writeable MIB's for all components of a devices configuration, it is also not secure depending on the version you are using. These were recognized as limitations by the IETF and as a result NETCONF was conceived with the following goals for automation of network device configuration:
- There must be a secure communication channel
- The protocol must include operations for making configuration changes as well as obtaining operational data and statistics
- It should have the capabilities to send PUSH notifications (similar to SNMP traps), either when an event happens or at regular intervals

NETCONF operations in a client/server model with the server being the network device and the client being a station the network administrator controls. NETCONF doesn't itself define the format of the data, it provides a means for communicating programmatically with network devices based on a set of defined operations. These operations allow you to get/edit/delete the configuration or portions of it, save the configuration, and get state information. NETCONF message use XML-formatted messages in RPC's to communicate with network devices, but don't be too discouraged by this as Python's ncclient makes this easy to work with.

NETCONF allows for multiple data stores on a device representing areas like the running-configuration, startup-configuration, or candidate-configuration. The idea of a candidate configuration is great because it allows for making configuration changes to the device without affecting the running-configuration directly!

## What is YANG?
YANG stands for "Yet another next generation" data model and is now used with NETCONF. Because NETCONF doesn't define how the data is represented, YANG provides a structured data model that represents your network devices configuration or the telemetry data you might be getting from it. YANG is expressed in XML, which is easy to read and write. Each network device must provide support for [YANG modules](https://github.com/YangModels/yang) (AKA namespaces), some of which are well-known and some which are vendor specific. These modules represent tree's within your configuration or state data that you can reference, and define the layout and the data types that might be returned (ex. binary, bits, int, string, etc). I don't think its necessary to understand how to write a YANG module, but it is certainly helpful to know how to read a module if you're ever needing to understand how to configure something and how it will be represented. That being said, this blog post identifies a more exploratory method that you can use with your network device directly.

## Enabling NETCONF on Cisco IOS-XE
Before we can communicate with a network device using NETCONF we need to enable the protocol first. NETCONF uses SSH as a transport and it is served on TCP port 830 by default on Cisco IOS-XE. I have a Cisco IOS-XE CSRv router running 16.3.5 in my home lab that I will be testing with. To enable NETCONF use the following commands:
```
R1#config t
Enter configuration commands, one per line.  End with CNTL/Z.
R1(config)#netconf-yang
```

To verify that the NETCONF processes are now functioning
```
R1#show platform software yang-management process
confd            : Running
nesd             : Running
syncfd           : Running
ncsshd           : Running
dmiauthd         : Running
vtyserverutild   : Running
opdatamgrd       : Running
ngnix            : Running
```

> You should take great care in ensuring that all the necessary security practices have been put in place to secure your network device. Enabling NETCONF, just like any other management protocol or feature, exposes another attack surface on your network device.

## Which modules are supported?
Not all network devices support all YANG modules out of the box, you may need to load modules for additional functionality. But, lets see how to identify which YANG modules are supported. We will be using Pythons ncclient library to communicate with the lab router.

To establish a NETCONF session with our router you can use the ncclient.manager.connect() function
```python
>>> from ncclient import manager
>>> host = '192.168.11.11'
>>> username = 'admin'
>>> password = 'badpassword'
>>> port = '830'
>>> device = manager.connect(host=host, username=username, password=password, port=port)
>>> device
<ncclient.manager.Manager object at 0x107e594c0>
```

The device variable is an ncclient.manager.Manager object which exposes additional functionality for communicating with your network device using NETCONF. To see which modules the network device has available we can use the device.server_capabilities iterator. This prints a very long list of capabilities, but these are the various YANG modules and namespaces we have available to us:
```python
>>> for cap in device.server_capabilities:
...     print(cap)
...
urn:ietf:params:netconf:base:1.0
urn:ietf:params:netconf:base:1.1
urn:ietf:params:netconf:capability:writable-running:1.0
urn:ietf:params:netconf:capability:xpath:1.0
urn:ietf:params:netconf:capability:validate:1.0
urn:ietf:params:netconf:capability:validate:1.1
urn:ietf:params:netconf:capability:rollback-on-error:1.0
urn:ietf:params:netconf:capability:notification:1.0
urn:ietf:params:netconf:capability:interleave:1.0
http://tail-f.com/ns/netconf/actions/1.0
http://tail-f.com/ns/netconf/extensions
urn:ietf:params:netconf:capability:with-defaults:1.0?basic-mode=report-all
urn:ietf:params:xml:ns:yang:ietf-netconf-with-defaults?revision=2011-06-01&module=ietf-netconf-with-defaults
http://cisco.com/ns/yang/ned/ios?module=ned&revision=2016-09-19
urn:cisco:params:xml:ns:yang:cisco-acl-oper?module=cisco-acl-oper&revision=2016-03-30
urn:cisco:params:xml:ns:yang:cisco-bfd-state?module=cisco-bfd-state&revision=2015-04-09
urn:cisco:params:xml:ns:yang:cisco-bgp-state?module=cisco-bgp-state&revision=2015-10-16
<<<SNIP>>>
```

## Obtaining the running-configuration
So back to our original problem of how to configure an interface description using NETCONF from the Reddit post, lets assume we don't know which of the above namespaces to use. I have manually configured an interface description on GigabitEthernet1:
```
R1#show int desc
Interface                      Status         Protocol Description
Gi1                            up             up       TEST DESCRIPTION
Gi2                            up             up
```

To get the current running-configuration using NETCONF we need to use the get_config() function in ncclient and specify a source data-store of 'running'. I'm using Python's xmltodict library to convert this to a Python dictionary to make this easy for us to read
```python
>>> import xmltodict
>>> xml_config = device.get_config(source='running').data_xml
>>> config = xmltodict.parse(xml_config)
```

Within this new dictionary we have various keys available to us:
```python
>>> config.keys()
odict_keys(['data'])
>>> config['data'].keys()
odict_keys(['@xmlns', '@xmlns:nc', 'native', 'netconf-yang', 'aaa', 'SNMPv2-MIB', 'interfaces', 'nacm', 'routing'])
```

The most likely key for us to find interface related information is the 'interfaces' key:
```python
>>> config['data']['interfaces'].keys()
odict_keys(['@xmlns', 'interface'])
>>> config['data']['interfaces']['@xmlns']
'urn:ietf:params:xml:ns:yang:ietf-interfaces'
```

I've shown above that the '@xmlns' key provides us with the namespace (`urn:ietf:params:xml:ns:yang:ietf-interfaces`) that is used to configure this part of the XML tree. But to see the actual configuration of an interface we need to now use the 'interface' key. This part of the dictionary is actually an ordered list of the interfaces and their configuration and you can see below that index 0 is GigabitEthernet1 with the description of 'TEST DESCRIPTION':
```python
>>> config['data']['interfaces']['interface'][0]
OrderedDict([('name', 'GigabitEthernet1'), ('description', 'TEST DESCRIPTION'), ('type', OrderedDict([('@xmlns:ianaift', 'urn:ietf:params:xml:ns:yang:iana-if-type'), ('#text', 'ianaift:ethernetCsmacd')])), ('enabled', 'true'), ('ipv4', OrderedDict([('@xmlns', 'urn:ietf:params:xml:ns:yang:ietf-ip')])), ('ipv6', OrderedDict([('@xmlns', 'urn:ietf:params:xml:ns:yang:ietf-ip')]))])
>>> config['data']['interfaces']['interface'][1]
OrderedDict([('name', 'GigabitEthernet2'), ('type', OrderedDict([('@xmlns:ianaift', 'urn:ietf:params:xml:ns:yang:iana-if-type'), ('#text', 'ianaift:ethernetCsmacd')])), ('enabled', 'true'), ('ipv4', OrderedDict([('@xmlns', 'urn:ietf:params:xml:ns:yang:ietf-ip'), ('address', OrderedDict([('ip', '192.168.11.11'), ('netmask', '255.255.255.0')]))])), ('ipv6', OrderedDict([('@xmlns', 'urn:ietf:params:xml:ns:yang:ietf-ip')]))])
```

## Modifying the configuration
To modify the interface description of GigabitEthernet1 to something new we first need to identify XML YANG data that we will be sending back. Do so by creating a variable with this information:
```python
>>> new_desc = """
... <config>
... <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
... <interface>
... <name>GigabitEthernet1</name>
... <description>NEW DESCRIPTION</description>
... </interface>
... </interfaces>
... </config>"""
```

The above variable shows that we are entering the `<config>` element and then the `<interfaces>` element and here we provide our namespace that we obtained previously. This particular namespace is a list of interfaces that are configured so we enter the `<interface>` namespace and provide a few variables including `<name>` to specify we want to modify GigabitEthernet1 as well as the new `<description>`. We can now send this data back to the network device using the edit_config() function and providing the target data-store of the running-configuration:
```python
resp = device.edit_config(new_desc, target='running')
>>> resp
<?xml version="1.0" encoding="UTF-8"?>
<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="urn:uuid:67934666-faf8-421c-a5db-b2b8809d3421" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0"><ok/></rpc-reply>
```

To confirm that this has been posted correctly to the device, you can see in the above `resp` variable that an RPC OK message was returned. We also see the interface description modified on the CLI of the device:
```
R1#show int desc
Interface                      Status         Protocol Description
Gi1                            up             up       NEW DESCRIPTION
Gi2                            up             up
```

## Saving the configuration
The above section on modifying the configuration only targetted the 'running' data-store, which is the running-configuration. If this device were to reload, that configuration change would be gone completely. The ncclient provides a commit() function, but that only works on devices that have candidate configuration capabilities enabled:

```python
>>> device.commit()
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/Users/byaklin/Documents/Training/Cisco/DEVASC/venv/lib/python3.9/site-packages/ncclient/manager.py", line 239, in execute
    return cls(self._session,
  File "/Users/byaklin/Documents/Training/Cisco/DEVASC/venv/lib/python3.9/site-packages/ncclient/operations/rpc.py", line 311, in __init__
    self._assert(cap)
  File "/Users/byaklin/Documents/Training/Cisco/DEVASC/venv/lib/python3.9/site-packages/ncclient/operations/rpc.py", line 386, in _assert
    raise MissingCapabilityError('Server does not support [%s]' % capability)
ncclient.operations.errors.MissingCapabilityError: Server does not support [:candidate]
```

Instead, I found on [Cisco DevNet's Github](https://github.com/CiscoDevNet/dne-dna-code/blob/master/intro-mdp/netconf/save_config.py) a method of using the cisco-ia:save-config namespace to accomplish this.
```python
# In addition to the manage import, also import xml_
>>> from ncclient import manager, xml_
# Create a new XML text string calling the save-config namespace
>>> save_config = """
... <cisco-ia:save-config xmlns:cisco-ia="http://cisco.com/yang/cisco-ia"/>"""
# Using the dispatch() function send an XML element
>>> resp = device.dispatch(xml_.to_ele(save_config))
# The response XML indicates that the running configuration was saved successfully!
>>> resp
<?xml version="1.0" encoding="UTF-8"?>
<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="urn:uuid:b41a1b19-c729-4e80-ab72-ac49dfd1a695" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0"><result xmlns='http://cisco.com/yang/cisco-ia'>Save running-config successful</result>
</rpc-reply>
```

And with that we have now modified the interface description in the running-configuration and saved it to the startup-configuration!

## Interested in learning more?
If you're interested in learning more, check out Cisco's DevNet Learning Labs, specifically the [IOS-XE Programmability](https://developer.cisco.com/learning/tracks/iosxe-programmability) lab that covers NETCONF and RESTCONF.