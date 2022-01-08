---
title: "Simple SNMP Queries with Python"
tags:
  - Python
  - Automation
  - SNMP
---

The need to query network devices for information on a repeated and consistent basis always been a critical function of performing network management. Monitoring the health of your network devices, building reports for use by management, querying the status of a particular function, and so on. There are an increasing number of ways to perform this type of data gathering. From the extremes of manually logging in to run a CLI command or check a web GUI, to using the latest API or Netconf, network engineers have their choice of protocol to use. However, nothing is as common and widely deployed as Simple Network Management Protocol (SNMP). Most network monitoring platforms will rely on using SNMP, especially if a particular network platform is a decentralized platform like common routers and switches, requiring each network device to be queried individually instead of through a centralized controller.

Because of SNMP's common use, this article covers how you can use [PySNMP](https://pysnmp.readthedocs.io/en/latest/) and Python to programmatically querying your network devices. This will not be an introduction to SNMP. If you're looking to brush up on your SNMP knowledge, PySNMP actually has an SNMP [history](https://pysnmp.readthedocs.io/en/latest/docs/snmp-history.html) and [design](https://pysnmp.readthedocs.io/en/latest/docs/snmp-design.html) page you may find useful.

## What is PySNMP?

[PySNMP](https://pysnmp.readthedocs.io/en/latest/) is a Python package used for all manners of SNMP related functions. You can use the package to send SNMP GET or GETNEXT requests, send SNMP traps, or act as an SNMP agent which will respond to SNMP requests. I will be focusing on the GET and GETNEXT requests. PySNMP also supports all versions of SNMP, most of my examples below will be SNMP version 2c followed by a brief section covering how to use SNMP v3. There are a lot of features with this package, such as methods for performing asynchronous SNMP queries, but I will just be touching on the high-level API.

> It should be pointed out that the PySNMP packages latest release of 4.4.12 was last released on Sept 24, 2019 as seen on [Github](https://github.com/etingof/pysnmp). The [PySNMP](https://pysnmp.readthedocs.io/en/latest/) site itself has a disclaimer right at the top that the documentation is an inofficial copy.

I'm not entirely sure what has happened with the development of the PySNMP package, but it still seems to be commonly used. In my research of finding SNMP packages for use with Python, PySNMP is by far the most complete and feature-rich package. In fact, Ansible's [general community role](https://galaxy.ansible.com/community/general) still uses PySNMP for the [snmp_facts module](https://github.com/ansible-collections/community.general/blob/main/plugins/modules/net_tools/snmp_facts.py).

## A Note on Secrets

The code examples within this document hard code SNMP community values and SNMP v3 USM auth/priv information. DO NOT do this in production. Instead, use a secrets manager that you can programmatically query and/or environment variables. Always ensure that you are not hard coding secrets and commiting them to source control.

# Getting Started with PySNMP

In the examples I present in this post I have chosen to use the Ansible [snmp_facts](https://github.com/ansible-collections/community.general/blob/main/plugins/modules/net_tools/snmp_facts.py) method of SNMP queries with PySNMP instead of the method presented in the [PySNMP quick start](https://pysnmp.readthedocs.io/en/latest/quick-start.html) documentation. I have found Ansible's method far easier to use for any queries to network devices for OID's not already in the standard MIB's that PySNMP can reference. PySNMP appears to be unable to take in standard MIB files and instead requires that they be converted to a specific [PySNMP format](https://github.com/etingof/pysnmp-mibs) using [PySMI mibdump tool](https://github.com/etingof/pysmi/blob/master/scripts/mibdump.py). I have found this tool difficult to use, so for simplicity I will use the Ansible method of performing SNMP queries which uses OID's directly.

Lets start with a simple example of using SNMP v2c to send a query to a network device for sysName.

```python
import sys
from pysnmp.entity.rfc3413.oneliner import cmdgen

SYSNAME = '1.3.6.1.2.1.1.5.0'

host = '10.1.1.1'
snmp_ro_comm = 'mysnmprocomm'

# Define a PySNMP CommunityData object named auth, by providing the SNMP community string
auth = cmdgen.CommunityData(snmp_ro_comm)

# Define the CommandGenerator, which will be used to send SNMP queries
cmdGen = cmdgen.CommandGenerator()

# Query a network device using the getCmd() function, providing the auth object, a UDP transport
# our OID for SYSNAME, and don't lookup the OID in PySNMP's MIB's
errorIndication, errorStatus, errorIndex, varBinds = cmdGen.getCmd(
    auth,
    cmdgen.UdpTransportTarget((host, 161)),
    cmdgen.MibVariable(SYSNAME),
    lookupMib=False,
)

# Check if there was an error querying the device
if errorIndication:
    sys.exit()

# We only expect a single response from the host for sysName, but varBinds is an object
# that we need to iterate over. It provides the OID and the value, both of which have a
# prettyPrint() method so that you can get the actual string data
for oid, val in varBinds:
    print(oid.prettyPrint(), val.prettyPrint())
```

To break down the above code a bit more, we query a host at IP address 10.1.1.1 with an SNMP v2c community string of mysnmprocomm for the sysName OID 1.3.6.1.2.1.1.5.0. This is performed by first importing PySNMP's oneliner cmdgen module which is a simplified method for performing SNMP queries versus the PySNMP high-level API (HLAPI). To use this module we first create a cmdgen CommandGenerator object which allows you to perform SNMP operations such as bulkCmd, getCmd, nextCmd and setCmd. In our example, we are using getCmd() which takes a few arguments:

- authData which we provide as an auth object created using cmdgen.CommunityData()
- A UDP transport which is where we provide the host IP address and common SNMP UDP port of 161
- A MIB variable which we have associated with our SYSNAME variables OID value
- An indication to not look the OID up in PySNMP's provided MIB references

When issuing the getCmd() command it will return four variables

- errorIndication - A string that when present indicates an SNMP error, along with the provided text of the error
- errorStatus - A string that when present indicates an SNMP PDU error
- errorIndex - The index in varBinds that generated the error
- varBinds - A sequence of MIB variable values returned via SNMP. These are [PySNMP ObjectType](https://pysnmp.readthedocs.io/en/latest/docs/api-reference.html#pysnmp.smi.rfc1902.ObjectType) class instances

To explore the errorIndication variable further, lets say that the host is not responding to SNMP. After calling the cmdgen.getCmd() function and getting the four returned values, a host thats non-responsive would look as follows (below):

```python
>>> errorIndication, errorStatus, errorIndex, varBinds = cmdGen.getCmd(
...     auth,
...     cmdgen.UdpTransportTarget((host, 161)),
...     cmdgen.MibVariable(SYSNAME),
...     lookupMib=False,
... )
>>> errorIndication
RequestTimedOut('No SNMP response received before timeout')
>>> varBinds
()
```

So errorIndication has an actual string value associated with it indicating that the request timed out, and varBinds is an empty Tuple. Lets look at what happens when the host is reachable and responds to sysName:

```python
>>> errorIndication, errorStatus, errorIndex, varBinds = cmdGen.getCmd(
...     auth,
...     cmdgen.UdpTransportTarget((host, 161)),
...     cmdgen.MibVariable(SYSNAME),
...     lookupMib=False,
... )
>>> len(varBinds)
1
>>> varBinds
[(<ObjectName value object, tagSet <TagSet object, tags 0:0:6>, payload [1.3.6.1.2.1.1.5.0]>, <OctetString value object, tagSet <TagSet object, tags 0:0:4>, subtypeSpec <ConstraintsIntersection object, consts <ValueSizeConstraint object, consts 0, 65535>>, encoding iso-8859-1, payload [myrouter.yaklin.ca]>)]
>>> for oid, val in varBinds:
...     print(oid.prettyPrint(), val.prettyPrint())
...
1.3.6.1.2.1.1.5.0 myrouter.yaklin.ca
```

You can see that the actual varBinds Tuple contains a single entry witih multiple parameters. If we iterate over that entry we can get the OID which was returned, along with the value.

> Why would the returned OID be needed? Shouldn't we already know which OID we queried? You'll see that when querying using the nextCmd() method for a table of OID's, such as when querying the status of each interface on a device, you will need the returned OID as it will contain the high-level OID (e.g. 1.3.6.1.2.1.2.2.1.8 for ifOperStatus), concatenated with the ifIndex value for the interface

## Querying Multiple OID's at Once

It turns out that you can actually provide multiple OID's to PySNMP's getCmd() method. If we wanted to query for both sysName and sysDescr, we could do so as follows (below I am only showing a subset of the code instead of repeating what was shown in the first example above):

```python
SYSDESCR = '1.3.6.1.2.1.1.1.0'
SYSNAME = '1.3.6.1.2.1.1.5.0'

# Create a Tuple of the OID's that you want to query
oids = (SYSNAME, SYSDESCR)

errorIndication, errorStatus, errorIndex, varBinds = cmdGen.getCmd(
    auth,
    cmdgen.UdpTransportTarget((host, 161)),
    *[cmdgen.MibVariable(oid) for oid in oids],
    lookupMib=False,
)
```

Now when we inspect varBinds we see we have two variable responses. One for sysName and the other for sysDescr:

```python
>>> len(varBinds)
2
>>> for oid, val in varBinds:
...     print(oid.prettyPrint(), val.prettyPrint())
...
1.3.6.1.2.1.1.5.0 myrouter.yaklin.ca
1.3.6.1.2.1.1.1.0 0x436973636f20494f5320536f6674776172652c203238303020536f667477617265202843323830304e4d2d414456454e54455250524953454b392d4d292c2056657273696f6e2031322e3428313363292c2052454c4541534520534f4654574152452028666332290d0a546563686e6963616c20537570706f72743a20687474703a2f2f7777772e636973636f2e636f6d2f74656368737570706f72740d0a436f707972696768742028632920313938362d3230303720627920436973636f2053797374656d732c20496e632e0d0a436f6d70696c6564205468752031342d4a756e2d30372031383a35312062792070726f645f72656c5f7465616d
```

> The sysDescr response is actually a hex representation that needs to be decoded. This is outside the scope of this post, but I would recommend reviewing the Ansible [snmp_facts](https://github.com/ansible-collections/community.general/blob/main/plugins/modules/net_tools/snmp_facts.py) module and its decode_hex() and to_text() functions.

## Querying an SNMP table using nextCmd()

To query an SNMP table for details you need to use the nextCmd() function. This is very similar to the getCmd() function, with only some minor adjustments. SNMP tables are used for data such as interface details (admin or operational up/down status, duplex, speed, etc) and metrics (bytes in/out, errors, discards, etc), the physical inventory of a device (such as entPhysicalModelName for querying Cisco's EoX API - Check out my posts on the API's in [part 1]({% post_url 2021-02-01-guide-to-cisco-support-apis-part-1 %}) and [part 2]({% post_url 2021-02-07-guide-to-cisco-support-apis-part-2 %})).

Below I present a complete code snippet highlighting its use. I have adjusted the comments specific to the changes from the previous snippet.

```python
import sys
from pysnmp.entity.rfc3413.oneliner import cmdgen

IFOPERSTATUS = '1.3.6.1.2.1.2.2.1.8'

host = '10.1.1.1'
snmp_ro_comm = 'mysnmprocomm'

auth = cmdgen.CommunityData(snmp_ro_comm)
cmdGen = cmdgen.CommandGenerator()

# Query a network device using the nextCmd() function. We're providing the ifOperStatus
# OID and expect an SNMP table response, which we will call varTable
errorIndication, errorStatus, errorIndex, varTable = cmdGen.nextCmd(
    auth,
    cmdgen.UdpTransportTarget((host, 161)),
    cmdgen.MibVariable(IFOPERSTATUS),
    lookupMib=False,
)

if errorIndication:
    sys.exit()

# We can now iterate over each interface to get its operational status
for varBinds in varTable:
    for oid, val in varBinds:
        print(oid.prettyPrint(), 'Operational Status', val.prettyPrint())
```

When using nextCmd() it will return a table of varBinds, so we need to iterate first over the table and then over the varBinds. The results of this query to my test router show four interfaces with their operational status. The values for ifOperStatus are numeric values representing the [operational status](http://www.net-snmp.org/docs/mibs/interfaces.html) where a response value of 1 means the interface is operationally up and 2 means it is down.

```python
>>> for varBinds in varTable:
...     for oid, val in varBinds:
...         print(oid.prettyPrint(), 'Operational Status', val.prettyPrint())
...
1.3.6.1.2.1.2.2.1.8.1 Operational Status 2
1.3.6.1.2.1.2.2.1.8.2 Operational Status 1
1.3.6.1.2.1.2.2.1.8.3 Operational Status 2
1.3.6.1.2.1.2.2.1.8.5 Operational Status 1
```

You'll also see in the above output that although we queries for the OID of 1.3.6.1.2.1.2.2.1.8, we now see each response OID has the ifIndex value (1, 2, 3, and 5 in the above example) appended to the end. This can allow you to query for ifName and ifDescr so that you can provide more human readable details around which interfaces are up and down.

## Querying using SNMP v3

Many SNMP deployements that I come across are still using SNMP v1 or v2c versions which are insecure as the queries and responses are not encrypted. If you're fortunate enough to work in an SNMP v3 environment, you need to adjust how you create the auth credentials provided to getCmd() and nextCmd(). If you're still using SNMP v1 or v2c, there's never a better time than now to advocate for SNMP v3, or another method of obtaining telemetry through a protocol that uses strong authentication and encryption.

There are multiple parameters that need to be provided to create an SNMP v3 auth credential to provide to getCmd() and nextCmd(). The following shows a common example using SHA512 and AES256 with SNMP v3, and how to create the auth object for further use by these functions:

```python
import sys
from pysnmp.entity.rfc3413.oneliner import cmdgen

SYSNAME = '1.3.6.1.2.1.1.5.0'

host = '10.1.1.1'

# Define a PySNMP UsmUserData object named auth, by providing the SNMP v3 username,
# auth key and protocol, and priv key and protocol
auth = cmdgen.UsmUserData(userName='mysnmpuser',
                          authKey='myauthpassphrase',
                          authProtocol=cmdgen.usmHMAC384SHA512AuthProtocol,
                          privKey='myprivpassphrase',
                          privProtocol=cmdgen.usmAesCfb256Protocol)

cmdGen = cmdgen.CommandGenerator()
errorIndication, errorStatus, errorIndex, varBinds = cmdGen.getCmd(
    auth,
    cmdgen.UdpTransportTarget((host, 161)),
    cmdgen.MibVariable(SYSNAME),
    lookupMib=False,
)

if errorIndication:
    sys.exit()

for oid, val in varBinds:
    print(oid.prettyPrint(), val.prettyPrint())
```

PySNMP has classes that you can use for the auth and priv protocols in use by SNMP v3. The following are their class names:

- Auth Protocol Classes
  - cmdgen.usmHMACMD5AuthProtocol
  - cmdgen.usmHMACSHAAuthProtocol
  - cmdgen.usmHMAC128SHA224AuthProtocol
  - cmdgen.usmHMAC192SHA256AuthProtocol
  - cmdgen.usmHMAC256SHA384AuthProtocol
  - cmdgen.usmHMAC384SHA512AuthProtocol
  - cmdgen.usmNoAuthProtocol (the default, if authProtocol is not provided)
- Priv Protocol Classes
  - cmdgen.usmDESPrivProtocol
  - cmdgen.usm3DESEDEPrivProtocol
  - cmdgen.usmAesCfb128Protocol
  - cmdgen.usmAesCfb192Protocol
  - cmdgen.usmAesCfb256Protocol
  - cmdgen.usmNoPrivProtocol (the default, if no privProtocol is provided)

## Wrapping Up

Using SNMP within Python doesn't have to be hard, and it offers an easier approach to obtaining device details and metrics without having to scrape CLI output with regular expressions. The data that you obtain can be used for all sorts of things including monitoring, reporting and troubleshooting. I have previously presented using the [Cisco EoX Support API]({% post_url 2021-02-07-guide-to-cisco-support-apis-part-2 %})) to query Cisco's site for end-of-life information, but I didn't provide a method to gather the list of product ID's programmatically from your network inventory. SNMP would be a great tool to get this information by querying entPhysicalModelName to get your list of product ID's. I'm hoping to write a post specifically about this in the near future!
