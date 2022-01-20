---
title: "Secure Queries with SNMPv3 and PySNMP"
tags:
  - Python
  - Automation
  - SNMP
description: How to send secure SNMP queries with Python's PySNMP and SNMPv3 credentials.
---

The information obtained with SNMP from network devices ranges from being simple timeseries type data like interface metrics to complex and sensitive status information about the features and protocols that the device is running. It is critical to protect this information when in transit between an SNMP agent and manager by utilizing SNMPv3. Sensitive data from network devices being sent in SNMP responses can be used by malicious parties to perform reconnaissance about your environment, learn which protocols and features you utilize, and prepare for a more specific attack based on the information that is learned.

The transit network between a network device that is being queried and the management stations performing the queries (where our Python code is located) often times runs over networks outside of an organizations control. MPLS networks, point-to-point circuits, etc. all are controlled by carriers and vendors and _you_ cannot guarantee the security of their environment. There are many ways in which you can protect the data that flows over these transits (e.g. IPSec), but often times may require complex design changes. While these types of design changes should be considered in the long-run, a quicker way of securing your SNMP queries is by utilizing SNMPv3.

## What is SNMPv3?

SNMP v1 and v2c send query and response data in clear-text form (along with the community string, which is supposed to be privileged information!). Anyone that is able to snoop the SNMP packets is able to read the data that is being exchanged. SNMP v3 primary goal is security of the messages/data being exchanged between SNMP managers and agents. It accomplishes this through a few different means:

- A user-based security model (USM) for securing SNMP messages with:
  - Authentication - Ensuring that whoever is sending an SNMP query is who they say they are
  - Encryption - Ensuring that the SNMP query and response have not been manipulated in transit
- A view-based access control model (VACM) for authorizing SNMP users access to specific MIB's on a network device

An additional aspect to SNMPv3's security is the snmpEngineId which is an identifier which must be unique to each SNMP entity. The snmpEngineId value is used by SNMP systems to add protection against [message replay, delay and redirection attacks](https://datatracker.ietf.org/doc/html/rfc3414#section-1.5).

Each networking manufacturer often defines a default snmpEngineId for each system, sometimes involving the systems MAC address to as to ensure uniqueness. This differs from vendor to vendor. Additionally, I have seen instances where a system two firewalls running in an active/standby cluster both utilize the same snmpEngineId by default which can cause issues for a network management platform trying to treat each system as a separate device. In most cases, networking vendors allow you to adjust the snmpEngineId manually to a value you choose.

## Using SNMPv3 with PySNMP

### Overview

Pythons [PySNMP](https://pysnmp.readthedocs.io/en/latest/) allows you to provide a UsmUserData object for the authData parameter of its command generators ([getCmd]({% post_url 2022-01-11-pysnmp-hlapi-overview %}), [nextCmd and bulkCmd]({% post_url 2022-01-16-bulk-data-gathering-with-pysnmp %})). In my previous articles covering these PySNMP command generators I used a CommunityData object which is used for SNMP v1 or v2c queries. In this article I will focus on creating a UsmUserData object and providing it to the getCmd command generator. We will be using both authentication and privacy

### Example Network Device SNMPv3 Configuration

In the example that follows I am using a Cisco IOSv router deployed in a [Cisco Modeling Labs](https://developer.cisco.com/docs/modeling-labs/) (CML) virtual environment. The router is configured for SNMPv3 as follows:

```
snmp-server group v3group v3 priv
snmp-server user snmpv3user v3group v3 auth sha myauthpassword priv aes 256 myprivpassword
```

Generally speaking, the same SNMPv3 configuration (group, user and passphrases) would be configured across all, or a group of, network devices in your environment. There are all sorts of additional configuration that can be made to control which SNMP MIB views and SNMP contexts that the SNMP group has access to.

### Generating a UsmUserData Object

PySNMP's [UsmUserData](https://pysnmp.readthedocs.io/en/latest/docs/api-reference.html#user-based) object is used to build SNMPv3 credentials. It takes the following parameters:

- A username matching that which is configured on the Cisco router
- An authentication protocol object and key
- An privacy/encryption protocol object and key

There are several additional parameters that UsmUserData takes, but they are not necessary for our SNMP queries and are outside the scope of this article.
{: .notice}

The authentication and encryption related parameters are actually considered optional. It depends entirely on if your network device is configured for no authentication or privacy (noAuthNoPriv), authentication (authNoPriv), or authentication and privacy (authPriv). The strongest form of security would be through using authentication and privacy together.

To create a UsmUserData object that we can use against the network device in my example, we would define it as follows in Python:

```python
from pysnmp.hlapi import UsmUserData, usmHMACSHAAuthProtocol, \
                         usmAesCfb256Protocol

auth = UsmUserData(
    userName='snmpv3user',
    authKey='myauthpassword',
    authProtocol=usmHMACSHAAuthProtocol,
    privKey='myprivpassword',
    privProtocol=usmAesCfb256Protocol
)
```

Because my router is configured for SHA1, the authProtocol is set to `usmHMACSHAAuthProtocol`. Additionally, the router is using AES256 encryption for privacy so the privProtocol is set to `usmAesCfb256Protocol`.

Available authProtocol options in PySNMP are:

- usmNoAuthProtocol (default is authKey not given)
- usmHMACMD5AuthProtocol (default if authKey is given)
- usmHMACSHAAuthProtocol
- usmHMAC128SHA224AuthProtocol
- usmHMAC192SHA256AuthProtocol
- usmHMAC256SHA384AuthProtocol
- usmHMAC384SHA512AuthProtocol

Available privProtocol options in PySNMP are:

- usmNoPrivProtocol (default is privhKey not given)
- usmDESPrivProtocol (default if privKey is given)
- usm3DESEDEPrivProtocol
- usmAesCfb128Protocol
- usmAesCfb192Protocol
- usmAesCfb256Protocol

There are several additional parameters that UsmUserData takes, but they are not necessary for our SNMP queries and are outside the scope of this article.

### Associating UsmUserData with PySNMP getCmd - Send a Query!

Now that the UsmUserData object has been created and stored as a variable named `auth`, we can use that to send an SNMP query using the getCmd command generator:

```python
from pysnmp.hlapi import SnmpEngine, UdpTransportTarget, ContextData, \
                         ObjectType, ObjectIdentity, getCmd
iterator = getCmd(
    SnmpEngine(),
    auth,
    UdpTransportTarget(('192.168.11.201', 161)),
    ContextData(),
    ObjectType(ObjectIdentity('SNMPv2-MIB', 'sysName', 0))
)

errorIndication, errorStatus, errorIndex, varBinds = next(iterator)
```

For additional information on what the above statements are doing, please reference my post on using [Python and PySNMP's HLAPI]({% post_url 2022-01-11-pysnmp-hlapi-overview %}) to send SNMP queries.
{: .notice--info}

In the above example, the `auth` variable is passed as the second argument to getCmd. The outcome that we expect is that the remote device 192.168.11.201 (my Cisco IOSv lab router) accepted the authentication and privacy protocols and passphrases as well as the username. The contents of varBinds should be the router name:

```python
>>> varBinds[0].prettyPrint()
'SNMPv2-MIB::sysName.0 = Router1.lab.yaklin.ca'
```

If you used an authentication protocol that the remote device doesn't support (e.g. usmHMAC384SHA512AuthProtocol instead of usmHMACSHAAuthProtocol) or an incorrect authentication passphrase, the following errorIndication would be seen:

```python
>>> errorIndication
WrongDigest('Wrong SNMP PDU digest')
```

In performing two separate tests where I set an incorrect privacy protocol and then set an incorrect privacy passphrase (with the correct privacy protocol), I thought that my router would have indicated an incorrect protocol was used but instead it simply ignored the request and PySNMP waited to time the request out:

```python
>>> errorIndication
RequestTimedOut('No SNMP response received before timeout')
```
