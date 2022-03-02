---
title: "Parse PySNMP Object Identities for MIB Variable Names"
tags:
  - Python
  - Automation
  - SNMP
description: Inspect PySNMP Object Identities using a MIB browser to get a list of the names of the MIB variable hierarchy.
teaser: /assets/images/edvard-alexander-rolvaag-E75ZuAIpCzo-unsplash.jpg
og_image: /assets/images/edvard-alexander-rolvaag-E75ZuAIpCzo-unsplash.jpg
---

After using SNMP [to query]({% post_url 2022-01-11-pysnmp-hlapi-overview %}) a remote device for a particular [ObjectType](https://pysnmp.readthedocs.io/en/latest/docs/api-reference.html#pysnmp.smi.rfc1902.ObjectType) and getting the response ObjectType (which includes the MIB identity and the corresponding value), it is useful to be able to programmatically parse the [PySNMP ObjectIdentity](https://pysnmp.readthedocs.io/en/latest/docs/api-reference.html#pysnmp.smi.rfc1902.ObjectIdentity). This allows you to read the OID hierarchy and get a list human-readable MIB variable names for each node in the list.

For example when querying for the contents of an SNMP table using the [PySNMP bulkCmd]({% post_url 2022-01-16-bulk-data-gathering-with-pysnmp %}) you will get a large number of ObjectType responses correlating with each variable in the table that you queried. You're most likely going to need to translate these responses into a different data structure; perhaps writing them to different columns in a database table, outputing to CSV file, or some other type of report. It is useful to understand which ObjectIdentity corresponds to which MIB variable name (which might represent your column in a CSV file, such as entPhysicalDescr) and perhaps an index value associated with that ObjectIdentity (e.g. entPhysicalIndex in the [entPhysicalTable](https://oidref.com/1.3.6.1.2.1.47.1.1.1)) as well as the response value. In this article I will be covering PySNMP's ObjectType [resolveWithMib()](https://pysnmp.readthedocs.io/en/latest/docs/api-reference.html#pysnmp.smi.rfc1902.ObjectIdentity.resolveWithMib) function so that we can read the full hierarchy of the MIB variable.

If you're not already familiar with PySNMP's bulkCmd for sending SNMP GETBULK requests check out my [previous post]({% post_url 2022-01-16-bulk-data-gathering-with-pysnmp %}) to get familiar with querying SNMP tables!
{: .notice--info}

## Getting Started

We're going to focus on using [entPhysicalTable](https://oidref.com/1.3.6.1.2.1.47.1.1.1) in this example. This table contains details on all of the physical components of a particular network device such as the power supplies, fans, modules and their descriptions, serial numbers and other aspects that might be useful. Each hardware component is assigned a unique index value that is called entPhysicalIndex. You'll need a copy of the [ENTITY-MIB.my](https://github.com/brianyaklin/net-hw-inventory/blob/main/mib/ENTITY-MIB.my) file and we will be following the PySNMP example for the [SNMP MIB Browser](https://pysnmp.readthedocs.io/en/latest/examples/smi/manager/browsing-mib-tree.html#snmp-mib-browser) pretty closely.

## Building a MIB Browser

To build our MIB browser we need to import the builder, view, and compiler modules from pysnmp.smi and use them as follows:

```python
from pysnmp.smi import builder, view, compiler

MIB_FILE_SOURCE = 'file://.'

mib_builder = builder.MibBuilder()
compiler.addMibCompiler(mib_builder, sources=[MIB_FILE_SOURCE, ])
mib_builder.loadModules('ENTITY-MIB',)
mib_view = view.MibViewController(mib_builder)
```

In the above code we do a few different things:

- We import the necessary modules from pysnmp.smi
- We create a mib_builder class instance
- With the compiler module we tell PySNMP where to find our ENTITY-MIB.my file (which based on `file://.` is located in the same folder as where we're running the Python interpreter or our script, but you can specify a different path if your MIB file is located elsewhere). Note that the sources parameter allows you to provide multiple locations for MIB files
- We then load the ENTITY-MIB.my file into our mib_builder class instance, followed by building a view of that MIB in the mib_view class instance

With PySNMP's MIB builder module we don't need to [pre-compile the MIB]({% post_url 2022-01-14-compiling-mibs-for-pysnmp %}) file into PySNMP format, we can leave it as the plain-text file.
{: .notice--info}

You'll see in a later section how we'll use the mib_view class instance, which contains a reference to the ENTITY-MIB, to parse response objects of the entPhysicalTable SNMP table.

## Querying the entPhysicalTable SNMP table

I have covered in other articles how to query [SNMP tables]({% post_url 2022-01-16-bulk-data-gathering-with-pysnmp %}), so this will just be a quick bit of code to get us started. We are going to query a device at IP address 192.168.11.201 which is a virtual router in my home lab. Unfortunately it doesn't have much in terms of a values in the entPhysicalTablel but will work for this example anyways.

The code is as follows:

```python
from pysnmp.hlapi import SnmpEngine, UdpTransportTarget,\
    ContextData, ObjectType, ObjectIdentity, bulkCmd
from pysnmp.hlapi import CommunityData
from pysnmp.smi import builder, view, compiler

auth = CommunityData('rostring', mpModel=1)
object_type = ObjectType(ObjectIdentity(
    'ENTITY-MIB', 'entPhysicalTable'
).addAsn1MibSource('file://.'))

iterator = bulkCmd(
    SnmpEngine(),
    auth,
    UdpTransportTarget(('192.168.11.201', 161)),
    ContextData(),
    0, 200,
    object_type,
)

error_indication, error_status, error_index, var_binds = next(iterator)
```

If we take a look at the returned var_binds you can see that there is a single entry. Depending on the network device that you are querying for entPhysicalTable there can be a few values (such as a single value for my virtual router) or hundreds of values (in the case of larger network devices like modular switches):

```python
>>> len(var_binds)
1
>>> var_binds[0].prettyPrint()
'ENTITY-MIB::entPhysicalDescr.1 = IOSv chassis, Hw Serial#: 9ZEB8BXGIB6LD28LWUY1O, Hw Revision: 1.0'
```

## Inspecting ObjectIdentity's with a PySNMP MIB View

In the previous section we were returned a single value for the entPhysicalTable, but lets just assume that we were returned multiple values. What we need to do is be able to parse the `ENTITY-MIB::entPhysicalDescr.1` ObjectIdentity so that we can identify which particular MIB variable (entPhysicalDescr) and index value the var_bind was for. If you were just to use `var_bind[0][0]` you would get a string value of the entire OID chain of the variable name:

```python
>>> print(var_binds[0][0])
1.3.6.1.2.1.47.1.1.1.1.2.1
```

You could use PySNMP's prettyPrint() function on the ObjectIdentity, but that just gives us the human-readable name of the fully qualified path for the MIB variable:

```python
>>> print(var_binds[0][0].prettyPrint())
ENTITY-MIB::entPhysicalDescr.1
```

What we can do is use the mib_view class instance that we previously created. Lets first take a look at what this mib_view is. We can see that it is a MIB View controller:

```python
>>> type(mib_view)
<class 'pysnmp.smi.view.MibViewController'>
```

If you want to see the various class functions that it has, try using Python's built-in help function like so: `help(mib_view)`. You can see that there is a class function called getNodeName(), which actually takes in an ObjectIdentity class and will return the oid, an ordered label tuple with human-readable entries, and the suffix which in our case is the entPhysicalIndex value. We use getNodeName() as follows:

```python
oid, label, suffix = mib_view.getNodeName((var_binds[0][0]))
>>> oid.prettyPrint()
'1.3.6.1.2.1.47.1.1.1.1.2'
>>> label
('iso', 'org', 'dod', 'internet', 'mgmt', 'mib-2', 'entityMIB', 'entityMIBObjects', 'entityPhysical', 'entPhysicalTable', 'entPhysicalEntry', 'entPhysicalDescr')
>>> suffix.prettyPrint()
'1'
```

With the label we can extract that the response MIB variable binding was for entPhysicalDescr and it was for entPhysicalIndex number 1. In instances where you have many variables in the entPhysicalTable you will need to iterate over the var_binds response object that we queried using the bulkCmd and extract the last value of the label for each as well as the suffix by using the mib_view's getNodeName() class function. The results can then be stored in a Python Dict or List so that you can later write the results where you are storing or reporting on them (e.g. a database, CSV file, etc.)

## A Complete Example

To see a complete example of using PySNMP's bulkCmd, querying entPhysicalTable, parsing
the returned ObjectIdentities and building a hardware inventory report, check out my [network hardware inventory](https://github.com/brianyaklin/net-hw-inventory) project on Github!
