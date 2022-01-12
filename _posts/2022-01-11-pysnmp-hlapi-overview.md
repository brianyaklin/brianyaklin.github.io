---
title: "SNMP Queries with PySNMP High-Level API"
tags:
  - Python
  - Automation
  - SNMP
---

I've [previously written]({% post_url 2021-08-25-snmp-queries-with-python %}) about [PySNMP's](https://pysnmp.readthedocs.io/en/latest/) simpler SNMP query using one-liner command generator as a method to send SNMP queries using an OID. That method allows you to avoid having to compile MIB's that do not come as a default in the PySNMP library. In the next few posts I want to outline how to use PySNMP's high-level API (hlapi) and how to complie any MIB's that may be missing. This will help you use PySNMP in its intended fashion, and using the name of the OID which provides for better readability.

> To get a very high-level summary of PySNMP please check out my [previous post]({% post_url 2021-08-25-snmp-queries-with-python %}) near the top.

Within this article I will explore PySNMP's hlapi by breaking down it's own [quick start 'fetch SNMP variable](https://pysnmp.readthedocs.io/en/latest/quick-start.html) example. The hlapi was designed to be an easy to use API for as close to a 'one-liner' SNMP query as you can get. The examples in this guide will focus on the synchronous implementation (performing one SNMP task at a time), but there is the capability to implement PySNMP asynchronously if you are looking for increased speed and scalability.

## Getting Started - A Simple SNMP Query

We will start with a simple SNMP query using the method described in PySNMP's Quick Start linked above. In this particular example I am sending an SNMP GET to a Cisco IOSv router for sysName.

```python
from pysnmp.hlapi import SnmpEngine, CommunityData, UdpTransportTarget,\
                         ContextData, ObjectType, ObjectIdentity, getCmd

iterator = getCmd(
    SnmpEngine(),
    CommunityData('rostring', mpModel=1),
    UdpTransportTarget(('192.168.11.201', 161)),
    ContextData(),
    ObjectType(ObjectIdentity('SNMPv2-MIB', 'sysName', 0))
)

errorIndication, errorStatus, errorIndex, varBinds = next(iterator)

if errorIndication:
    print(errorIndication)
elif errorStatus:
    print('{} at {}'.format(errorStatus.prettyPrint(),
                        errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))

for oid, val in varBinds:
    print(f'{oid.prettyPrint()} = {val.prettyPrint()}')
```

When the above code is ran, the following is the output that we get:

```python
>>> for oid, val in varBinds:
...     print('{} = {}'.format(oid.prettyPrint(), val.prettyPrint()))
...
SNMPv2-MIB::sysName.0 = Router1.lab.yaklin.ca
```

To summarize what happened from a high-level:

1. All necessary modules were imported to build an SNMP query
2. An iterator was created which associates the various components of the SNMP query
3. The query is sent to the router by referring to the iterator with next() and the resulting response and any errors are stored across four variables
4. Checks are performed to see if any errors were picked up
5. The returned value for sysName is printed to screen

The remaining sections of this article will explain each of these points in further detail.

## Installing PySNMP

PySNMP runs with Python 2.4 through 3.7 according to the documentation, but I have been able to use its hlapi with Python 3.9.4. This doesn't guarantee that it will be stable with anything higher than 3.7.

To install PySNMP to work with Python 3.9.4, use:

```
python3 -m pip install pysnmp
```

> It should be pointed out that the PySNMP packages latest release of 4.4.12 was last released on Sept 24, 2019 as seen on [Github](https://github.com/etingof/pysnmp). The [PySNMP](https://pysnmp.readthedocs.io/en/latest/) site itself has a disclaimer right at the top that the documentation is an inofficial copy.

## PySNMP Modules for a Simple SNMP GET

### Importing the necessary components

Once you have PySNMP installed its time to import the various modules. The quick start tutorial uses [wildcard imports](https://www.python.org/dev/peps/pep-0008/#imports) as follows:

```python
from pysnmp.hlapi import *
```

The above method is discouraged in the PEP8 style guide for all the reasons mentioned in the link and as a result I import each module by name so as to avoid confusion. This makes it obvious when reviewing code as to where names are coming from:

```python
from pysnmp.hlapi import SnmpEngine, CommunityData, UdpTransportTarget,\
                         ContextData, ObjectType, ObjectIdentity, getCmd
```

### SnmpEngine() and ContextData()

The [SnmpEngine()](https://pysnmp.readthedocs.io/en/latest/docs/api-reference.html#high-level-v3arch-snmp-engine) class creates an SNMP engine object which helps to maintain state information associated with the SNMP query. [ContextData()](https://pysnmp.readthedocs.io/en/latest/docs/api-reference.html#high-level-v3arch-snmp-context) is described by PySNMP as _Creates UDP/IPv6 configuration entry and initialize socket API if needed_ and also assists in forming SNMP PDU's.

There are multiple parameters that can be passed to both SnmpEngine() and ContextData(), but they are not necessary for our purpuses and so won't be discussed further. Just know that you need to provide them to getCmd() without any parameters as shown in the example code above.

### CommunityData()

To provide SNMPv1 or v2 community strings to PySNMP we form an instance of PySNMP's [CommunityData()](https://pysnmp.readthedocs.io/en/latest/docs/api-reference.html#community-based) class and pass it our community string and if we're using SNMP v1 or v2c:

```python
CommunityData('rostring', mpModel=1)
```

In this case, 'rostring' is the community string and `mpModel=1` indicates SNMPv2c (`mpModel=0` would be for SNMPv1).

> Check out the [UsmUserData()](https://pysnmp.readthedocs.io/en/latest/docs/api-reference.html#user-based) class to learn more about using SNMPv3

### UdpTransportTarget()

To define which host you want to query via SNMP you use [UdpTransportTarget()](https://pysnmp.readthedocs.io/en/latest/docs/api-reference.html#transport-configuration). The first, and only required, parameter of this method is a tuple representing the hostname or IP address and the UDP port as an integer:

```python
UdpTransportTarget(('192.168.11.201', 161)),
```

A few additional parameters can be provided as well, if you need to control timeout intervals and retries. If not provided, a timeout of 1 second and 5 retries are the default values, but to adjust them the UdpTransportTarget() can be set as follows

```python
UdpTransportTarget(('192.168.11.201', 161), timeout=3, retries=10),
```

### ObjectType() and ObjectIdentity()

The combination of an [ObjectType()](https://pysnmp.readthedocs.io/en/latest/docs/api-reference.html#pysnmp.smi.rfc1902.ObjectType) encapsulating an [ObjectIdentity()](https://pysnmp.readthedocs.io/en/latest/docs/api-reference.html#mib-variables) defines which SNMP MIB variable we are going to query on the remote device. In this example sysName is being queried and is represented as follows:

```python
ObjectIdentity('SNMPv2-MIB', 'sysName', 0)
```

Starting with ObjectIdentity() we can see that our example takes three prameters:

- The MIB name, in this case SNMPv2-MIB
- The MIB variable, in this case sysName
- The instance of the MIB variable, which is 0 in our case for sysName

The combination of the three of these parameters represents the entire MIB variable ID of SNMPv2-MIB::sysName.0, or its OID of 1.3.6.1.2.1.1.5.0.

Note that when using the the method shown in our example, which makes for a more human-readable variable, is only possible if you the MIB object you are querying is part of a MIB pre-compiled into PySNMP's format using PySMI. PySNMP ships with several common MIB's compiled in the format you may need, but if you are needing to query a MIB object that isn't compiled you can specify it using the integers representing the OID either as a string or as a tuple of integers.

```python
ObjectIdentity('1.3.6.1.2.1.1.5.0')
ObjectIdentity((1,3,6,1,2,1,1,5,0))
```

> If you don't have a compiled MIB for the OID that you are querying, the output of the ObjectIdentity on the returned value will be the OID instead of a human-readable value. See the section below on compiled MIB's with PySNMP.

ObjectType() encapsulates our ObjectIdentity() into a container which we can use with various SNMP commands. In this instance the only parameter that we provide to ObjectType is our ObjectIdentity():

```python
ObjectType(ObjectIdentity('SNMPv2-MIB', 'sysName', 0))
```

## Initiating a Query with getCmd()

To send an SNMP GET to a device we will be using [getCmd()](https://pysnmp.readthedocs.io/en/latest/docs/hlapi/v3arch/asyncore/sync/manager/cmdgen/getcmd.html). This creates a [Python generator](https://realpython.com/introduction-to-python-generators/) which creates an iterable object much _like_ a list.

getCmd() requires a minimum of five paramters passed to it (each of these will be explained in further detail in the sections below):

- An SNMP engine using SnmpEngine()
- An SNMP community string using CommunityData(), or SNMP v3 credentials with UsmUserData()
- A transport target, in this example we use an IPv4 so UdpTransportTarget()
- A UDP context using ContextData()
- One _or more_ SNMP ObjectType() classes representing MIB variables (in our case sysName)
- Any optional parameters lookupMib

By combining all of these elements with getCmd() we assign the resulting iterable object to a variable which we call _iterator_ in our case:

```python
iterator = getCmd(
    SnmpEngine(),
    CommunityData('rostring', mpModel=1),
    UdpTransportTarget(('192.168.11.201', 161)),
    ContextData(),
    ObjectType(ObjectIdentity('SNMPv2-MIB', 'sysName', 0))
)
```

The above Python statement doesn't actually initiate any network traffic. No SNMP query has been snet to our device yet. Instead, it simply creates an iterable object by using a Python generator and in our case actions are only taken once we iterate over this object.

To iterate over each sequential element in this iterator object we call it using Python's built-in next() function on it (`next(iterator)`). In this example there will only be a single element in this iterable because we only have a single MIB object of sysName, so next() is only called a single time as follows:

```python
errorIndication, errorStatus, errorIndex, varBinds = next(iterator)
```

By accessing the next available element in the iterator, the getCmd() iterator returns four values:

- errorIndication - A string that when present indicates an SNMP error, along with the provided text of the error
- errorStatus - A string that when present indicates an SNMP PDU error
- errorIndex - The index in varBinds that generated the error
- varBinds - A sequence of MIB variable values returned via SNMP. These are [PySNMP ObjectType](https://pysnmp.readthedocs.io/en/latest/docs/api-reference.html#pysnmp.smi.rfc1902.ObjectType) class instances

> PySNMP supports other SNMP commands, such as bulkCmd(), nextCmd(), and setCmd(), by using the same generator/iterable approach.

## Querying Multiple SNMP OID's

As mentioned in the getCmd() section above, getCmd() is able to take a variable number of ObjectType's so as to facilitate querying multiple OID's. The below example queries for both sysName and sysDescr:

```python
iterator = getCmd(
    SnmpEngine(),
    CommunityData('rostring', mpModel=1),
    UdpTransportTarget(('192.168.11.201', 161)),
    ContextData(),
    ObjectType(ObjectIdentity('SNMPv2-MIB', 'sysName', 0)),
    ObjectType(ObjectIdentity('SNMPv2-MIB', 'sysDescr', 0))
)

errorIndication, errorStatus, errorIndex, varBinds = next(iterator)
```

If both MIB objects are available on the remote system, varBinds will have two elements (one for each OID). In this particular case we don't need to use next() twice, as both OID's are provided to the iterator at the same time. The values of each element can be seen as follows:

```python
>>> varBinds[0].prettyPrint()
'SNMPv2-MIB::sysName.0 = Router1.lab.yaklin.ca'
>>> varBinds[1].prettyPrint()
'SNMPv2-MIB::sysDescr.0 = Cisco IOS Software, IOSv Software (VIOS-ADVENTERPRISEK9-M), Version 15.9(3)M2, RELEASE SOFTWARE (fc1)\r\nTechnical Support: http://www.cisco.com/techsupport\r\nCopyright (c) 1986-2020 by Cisco Systems, Inc.\r\nCompiled Tue 28-Jul-20 07:09 by prod_rel_team'
```

## Error Checking of the SNMP Response

Each command generator (getCmd, nextCmd, bulkCmd, setCmd) return an errorIndication, errorStatus, errorIndex, and varBinds variable. The error related variables are described as follows:

- errorIndication: A string error message that when present indicates an SNMP Engine error
- errorState: A string error message that when present indicates an SNMP PDU error
- errorIndex: An integer that when non-zero indicates the position (n - 1) in varBinds that encountered the error

Common logic on assessing these variables after each command generator is run is as follows:

```python
if errorIndication:
    print(errorIndication)
elif errorStatus:
    print('{} at {}'.format(errorStatus.prettyPrint(),
                        errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
```

The above code first checks if there was an SNMP Engine error with errorIndication and if so prints it to screen. This is followed by checking if there is an SNMP PDU error with errorStatus and if so prints out the error message to screen followed by the index in varBinds and the value at varBinds. Of course when using SNMP at scale you may not be printing these to screen but updating a database or log file with the error that was encountered, adjusting additional logic to influence how the script treats the error for subsequent queries or analysis, or any other actions your script may need to make.

An example of what a timeout error might look like is by viewing the output of errorIndication when this is encountered:

```python
>>> errorIndication
RequestTimedOut('No SNMP response received before timeout')
```

## Parsing the Returned Response Data

Assuming you have gotten this far without any errors its now time to parse the response data in varBinds. PySNMP's generator commands describe varBinds as _A sequence of ObjectType class instances representing MIB variables returned in SNMP response_. We also know that an [ObjectType](https://pysnmp.readthedocs.io/en/latest/docs/api-reference.html#pysnmp.smi.rfc1902.ObjectType) instance represents the ObjectIdentity (which MIB variable was queried) and the payload that was returned in the response. This is useful because it tells us first which MIB variable is being returned (in our case sysName) and then what the value is. In our case we only queried sysName so its a safe assumption to make that we got a response for sysName, but in the example showed earlier where we queried for both sysName and sysDescr, it would be useful to know which element in the varBinds list corresponds to which MIB variable.

In our example of querying for sysName we can see that varBinds has the following structure:

```python
>>> len(varBinds)
1
>>> type(varBinds[0])
<class 'pysnmp.smi.rfc1902.ObjectType'>
>>> varBinds
[ObjectType(ObjectIdentity(<ObjectName value object, tagSet <TagSet object, tags 0:0:6>, payload [1.3.6.1.2.1.1.5.0]>), <DisplayString value object, tagSet <TagSet object, tags 0:0:4>, subtypeSpec <ConstraintsIntersection object, consts <ValueSizeConstraint object, consts 0, 65535>, <ValueSizeConstraint object, consts 0, 255>, <ValueSizeConstraint object, consts 0, 255>>, encoding iso-8859-1, payload [Router1.lab.yaklin.ca]>)]
```

There is a handy helper function called .prettyPrint() associated with ObjectType that can transform the whole response to a nice string by concatenating the MIB variable name and the response value together:

```python
>>> varBinds[0].prettyPrint()
'SNMPv2-MIB::sysName.0 = Router1.lab.yaklin.ca'
```

In most scripts we will only care about the returned value and this can be accessed by referring to the payload of the ObjectType:

```python
>>> varBinds[0][1].prettyPrint()
'Router1.lab.yaklin.ca'
```

## A Note on Compiled MIB's and PySNMP

PySNMP looks for MIB files in a few locations that have been compiled in a specific format that it understands. Out of the box PySNMP comes with a few standard MIB's pre-compiled and this helps with translating the MIB variable names when parsing the varBinds ObjectType() instances, as well as allowing us to reference these MIB variables by name when defining the ObjectType() we want to query.

In cases where we are querying based on an OID because we don't have a MIB pre-compiled, varBinds response variables are a bit more difficult to interpret. Take as an example the following varBinds variable that I queried which has a name of entPhysicalSerialNum and an OID of 1.3.6.1.2.1.47.1.1.1.1.11 so that I can get the serial number of a router (in this case at entPhysicalIndex of 1):

```python
iterator = getCmd(
    SnmpEngine(),
    CommunityData('rostring', mpModel=1),
    UdpTransportTarget(('192.168.11.201', 161)),
    ContextData(),
    ObjectType(ObjectIdentity('1.3.6.1.2.1.47.1.1.1.1.11.1'))
)

errorIndication, errorStatus, errorIndex, varBinds = next(iterator)
```

When looking at the response for varBinds you can see that the MIB variable name isn't fully translated by PySNMP:

```python
>>> varBinds[0].prettyPrint()
'SNMPv2-SMI::mib-2.47.1.1.1.1.11.1 = 9ZEB8BXGIB6LD28LWUY1O'
```

In an upcoming post I plan on highlighting how to compile MIB's so that you're able to reference a human readable name like entPhysicalIndex instead of its OID, and PySNMP in return is able to translate the OID back to a human readable name for you.
