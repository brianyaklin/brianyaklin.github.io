---
title: "Compiling SNMP MIB's for PySNMP"
tags:
  - Python
  - Automation
  - SNMP
last_modified_at: 2022-01-17T21:13:00-07:00
---

The ability to refer to a SNMP MIB variable by name is an important aspect for increasing readability and understanding of your Python scripts. [PySNMP](https://pysnmp.readthedocs.io/en/latest/) comes with several common pre-compiled MIB's in a format that its capable of using, but if you need to query a MIB variable it doesn't ship with, you're left refering to the variable as an SNMP OID. Having to remember what a particular OID is for, or creating a mapping table between a MIB variable name and its OID (such as a Python dictionary), can become tedious. Additionally, parsing a [PySNMP ObjectType](https://pysnmp.readthedocs.io/en/latest/docs/api-reference.html#pysnmp.smi.rfc1902.ObjectType) class instance that isn't fully translated to the MIB variable name can make things more complicated.

When you install PySNMP with PIP you also get [PySMI](https://github.com/etingof/pysmi) with it. PySMI was created by the same creator as PySNMP, and it allows you to compile other SNMP MIB's for your projects. This article will cover how to compile additional MIB's for your Python SNMP projects so that you can extend their capabilities!

Looking for an introduction to PySNMP? Check out my [previous post]({% post_url 2022-01-11-pysnmp-hlapi-overview %}) to get familiar!
{: .notice--info}

It should be pointed out that the PySNMP packages latest release of 4.4.12 was last released on Sept 24, 2019 as seen on [Github](https://github.com/etingof/pysnmp). The [PySNMP](https://pysnmp.readthedocs.io/en/latest/) site itself has a disclaimer right at the top that the documentation is an inofficial copy. Although it has not been updated in quite some time, it still appears to be effective for performing SNMP queries with Python.
{: .notice--warning}

## PySNMP and MIB's

PySNMP comes pre-compiled with a few common MIB's for your use out-of-the-box. You can see which MIB's are pre-compiled by checking out your Python installations site-packages folder under pysnmp/smi/mibs. That being said, PySNMP will look in the following locations for other complied MIB's:

- Your PySNMP's installation folder under pysnmp/smi/mibs
- In your home directory under .pysnmp/mibs
- In any local directory or remote HTTP location that you specify when adding a plain-text MIB to your command generator (e.g. getCmd())

## Where to Find 3rd Party MIB Files

Each platform vendor (e.g. Cisco, Arista, F5, etc) will often create SNMP MIB's that customers can use for querying platform-specific features/statistics. Often times you can download these MIB files from a vendors website or directly from their product that you have installed in your environment.

Using Cisco as an example, they have an [SNMP object navigator](https://snmp.cloudapps.cisco.com/Support/SNMP/do/BrowseMIB.do?local=en&step=2) (Cisco CCO login required) that allows you to browse their _extensive_ list of SNMP objects and MIB's.

## Using Plain-Text MIB's

To use a plain-text MIB with your command generator you can provide an ObjectIdentity and ObjectType class instance that looks like the following:

```python
ObjectType(ObjectIdentity(
    'IF-MIB', 'ifInOctets', 1
    ).addAsn1MibSource(
        'file://.',
        'file:///usr/share/snmp',
    )
)
```

In this particular case we are creating a reference to the MIB variable ifInOctets in the IF-MIB SNMP MIB. By using [.addAsn1MibSource()](https://pysnmp.readthedocs.io/en/latest/docs/api-reference.html#pysnmp.smi.rfc1902.ObjectIdentity.addAsn1MibSource) we can provide multiple local or remote file locations for MIB files. In this particular case I have placed IF-MIB.my in the same directory that I'm running my script from (`file://.`), and have an alternative path to search (`file:///usr/share/snmp`), showing that its possible to refer to multiple locations. Additional locations can be remote HTTP sites to download the MIB from.

An example of using this ObjectType with a command generator is as follows:

```python
from pysnmp.hlapi import SnmpEngine, CommunityData, UdpTransportTarget,\
                         ContextData, ObjectType, ObjectIdentity, getCmd

iterator = getCmd(
    SnmpEngine(),
    CommunityData('rostring', mpModel=1),
    UdpTransportTarget(('192.168.11.201', 161)),
    ContextData(),
    ObjectType(ObjectIdentity(
        'IF-MIB', 'ifInOctets', 1
        ).addAsn1MibSource(
            'file://.'
        )
    )
)

errorIndication, errorStatus, errorIndex, varBinds = next(iterator)
```

You can see that our varBinds variable returns the number of Octets received on the interface with SNMP IF Index 1. The best part of this is that the MIB variable name is fully referenceable, instead of showing the OID:

```python
>>> varBinds[0].prettyPrint()
'IF-MIB::ifInOctets.1 = 81424'
```

## Compiling a MIB into PySNMP format

Referencing a plain-text MIB file works perfect fine for simple operations. However, I can see doing this at scale not being effective for the reason that the plain-text file needs to be read frequently, and if you're referring to a remote file location via HTTP this can add increased latency.

PySMI (which comes installed as a dependency when you install PySNMP) gives you the ability to take a plain-text file and compile it directly into a format that PySNMP can use. By using the `mibdump.py` utility that is made available to you with PySMI, you can provide a few flags and it will generate a PySNMP MIB Python file. In this case we will use the IF-MIB as an example of compiling. Using [Cisco's SNMP Object Navigator](https://snmp.cloudapps.cisco.com/Support/SNMP/do/BrowseMIB.do?local=en&step=2&submitClicked=true&mibName=IF-MIB#dependencies) search for and download the IF-MIB and open it in a text editor.

At the top of the IF-MIB.my file you'll see that there are a series of IMPORTS statements:

```
...

IMPORTS
    MODULE-IDENTITY, OBJECT-TYPE, Counter32, Gauge32, Counter64,
    Integer32, TimeTicks, mib-2,
    NOTIFICATION-TYPE                        FROM SNMPv2-SMI
    TEXTUAL-CONVENTION, DisplayString,
    PhysAddress, TruthValue, RowStatus,
    TimeStamp, AutonomousType, TestAndIncr   FROM SNMPv2-TC
    MODULE-COMPLIANCE, OBJECT-GROUP,
    NOTIFICATION-GROUP                       FROM SNMPv2-CONF
    snmpTraps                                FROM SNMPv2-MIB
    IANAifType                               FROM IANAifType-MIB;

...
```

These import statements refer to other MIB files that the IF-MIB relies on for declaring how to interpret the MIB file. In this particular case you will need to download all of the MIB files referenced after the `FROM` statements; SNMPv2-SMI, SNMPv2-TC, SNMPv2-CONF, SNMPv2-MIB, and IANAifType-MIB. Thankfully, these can be found at the same link I posted above.

The reason these files are important is because PySMI will need to refer to these when compiling IF-MIB, so that it can build a complete PySNMP referencable MIB file.

Once all of these files are downloaded and placed in a single folder, it's time to run `mibdump.py`:

```
(venv) snmp-testing % mibdump.py --generate-mib-texts --destination-format pysnmp IF-MIB
Source MIB repositories: file:///usr/share/snmp/mibs, http://mibs.snmplabs.com/asn1/@mib@
Borrow missing/failed MIBs from: http://mibs.snmplabs.com/pysnmp/fulltexts/@mib@
Existing/compiled MIB locations: pysnmp.smi.mibs, pysnmp_mibs
Compiled MIBs destination directory: /Users/byaklin/.pysnmp/mibs
MIBs excluded from code generation: INET-ADDRESS-MIB, PYSNMP-USM-MIB, RFC-1212, RFC-1215, RFC1065-SMI, RFC1155-SMI, RFC1158-MIB, RFC1213-MIB, SNMP-FRAMEWORK-MIB, SNMP-TARGET-MIB, SNMPv2-CONF, SNMPv2-SMI, SNMPv2-TC, SNMPv2-TM, TRANSPORT-ADDRESS-MIB
MIBs to compile: IF-MIB
Destination format: pysnmp
Parser grammar cache directory: not used
Also compile all relevant MIBs: yes
Rebuild MIBs regardless of age: no
Dry run mode: no
Create/update MIBs: yes
Byte-compile Python modules: yes (optimization level no)
Ignore compilation errors: no
Generate OID->MIB index: no
Generate texts in MIBs: yes
Keep original texts layout: no
Try various file names while searching for MIB module: yes
Created/updated MIBs:
Pre-compiled MIBs borrowed:
Up to date MIBs: IANAifType-MIB, IF-MIB, SNMPv2-CONF, SNMPv2-MIB, SNMPv2-SMI, SNMPv2-TC
Missing source MIBs:
Ignored MIBs:
Failed MIBs:
(venv) snmp-testing %
```

You can see that I provided a few flags:

- `--generated-mib-texts` so that we create a MIB file
- `--destination-format pysnmp` so that the output file format is in PySNMP, but the other option is JSON
- `IF-MIB` is the name of the MIB we want to compile. This searches for the IF-MIB.my file in the directory that you're running mibdump.py from

Note that you don't need to provide all of the name of the dependency MIB files. PySMI and mibdump.py can interpret IF-MIB.my to learn about these and search for them in the same directory.
{: .notice--info}

The output when running mibdump.py shows that the compiled MIB will be placed in the directory /Users/byaklin/.pysnmp/mibs (which PySNMP can search by default), but you can optionally provide a directory with the `--destination-directory` flag when running mibdump.py.

An alternative directory that you could store your compiled MIB file in would be that of where pysnmp is installed. In my case I'm using a Python virtual-environment, so the directory would be venv/lib/python3.9/site-packages/pysnmp/smi/mibs/

Now when we go to supply this MIB variable to our SNMP command, we don't need to reference an external source:

```python
iterator = getCmd(
    SnmpEngine(),
    CommunityData('rostring', mpModel=1),
    UdpTransportTarget(('192.168.11.201', 161)),
    ContextData(),
    ObjectType(ObjectIdentity('IF-MIB', 'ifInOctets', 1))
)
```
