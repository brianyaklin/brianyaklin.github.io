---
title: "Cisco IOS XE Netconf and Restconf Authentication Bypass Vulnerability"
tags:
  - Automation
  - Cisco
  - Security
  - Vulnerability
---

Earlier this week Cisco announced in its semiannual [Cisco IOS and IOS XE bundled software security advisory publication](https://tools.cisco.com/security/center/viewErp.x?alertId=ERP-74581) some very concerning security advisories (3 critical, 11 high and 11 medium severity), one of which allows an attacker to [bypass authentication on devices configured for netconf or restconf](https://tools.cisco.com/security/center/content/CiscoSecurityAdvisory/cisco-sa-aaa-Yx47ZT8Q). After an attacker has bypassed authentication, they can install, manipulate, or delete your Cisco IOS XE devices configuration or cause a memory corruption that results in a denial of service (DoS) condition.

This authentication bypass vulnerability has multiple conditions that must be met for a device to be considered vulnerable:

- The software version of Cisco IOS XE must match one of the ~140 impacted software versions. Review the CVRF file for a list of affected software versions or the software checker utility, both found at the [advisory link](https://tools.cisco.com/security/center/content/CiscoSecurityAdvisory/cisco-sa-aaa-Yx47ZT8Q)
- You must have have multiple features configured:
  - Authentication, Authorization, Accounting (AAA), and
  - Netconf or restconf, and
  - An **enable password** without an **enable secret** configured

To validate if the affected features are enabled use the following commands:

- Validating AAA is configured
  - **show running-config &#x7c; include aaa authentication login**
- Validating Netconf or Restconf is configured
  - **show running-config &#x7c; include netconf&#x7c;restconf**
- Validating the enable password and secret configuration
  - **show running-config &#x7c; include enable password&#x7c;secret**

## Remediating the Exposure

There are multiple steps that should be taken to remediate, or limit, the exposure to this vulnerability, as well as some best practices to follow when it comes to the affected features. These include:

- Re-issue secrets, passphrases, and keys
- Configure an enable secret and remove the enable password
- Configure Netconf and Restconf Service-Level ACL's
- Compare Configuration for Signs of Manipulation
- Upgrade to an Unaffected Cisco IOS XE Software Version

### Re-Issue Secrets, Passphrases, and Keys

Given that the vulnerability allows a remote attacker to manipulate the current configuration on an affected device, it would be best to consider the configuration compromised. Sensitive information stored within your Cisco IOS XE devices configuration could include:

- Local usernames and password
- Enable password
- Enable secret
- Keychains used for various different protocols
- Protocol authentication keys (routing protocols, FHRP's, VTP, IKE, NTP, TACACS+, RADIUS, etc)

> It's worth noting that the entire configuration file of your device should be considered sensitive. The protocols which you have enabled, the software version, IP addresses used, the physical connections, and administratively defined variables. All of this information can be used by an attacker to survey your infrastructure to prepare for another attack. Unfortunately, it can be quite difficult to change your network architecture simply because your configuration is potentially compromised. However, there are are best-practices that you can follow for [securing network device management functions](https://www.optanix.com/five-best-practices-for-securing-network-device-management-functions/) to reduce your exposure

I'll refere to the list of sensitive information above simply as _secrets_ going forward. Some of these secrets, depending on the feature that they are configured for, can be stored in clear-text or in an encrypted fashion. It is good to be in the habit of changing these secrets on a regular interval and using strong password requirements. By already having a process in place to programmatically change these secrets as part of regular lifecycle management, responding to a potential compromise becomes far easier. By using a tool such as [Ansible](https://www.ansible.com/), you can lifecycle secrets across multiple different device vendors and models (among so many other network management tasks!)

### Configure an Enable Secret

Cisco's [IOS hardening guide](https://www.cisco.com/c/en/us/support/docs/ip/access-lists/13608-21.html#anc14) has long recommended using an **enable secret** instead of an **enable password** for securing privileged administrative access. Although this particular authentication bypass vulnerability also relies on AAA having been configured (wherein you would most likely be using an external service for authorizing privileged access), simply having an enable password configured in addition to AAA is one of the conditions for exposure. Even with AAA enabled, it is still recommended to configure a local enable secret in the event that your external AAA serves are not reachable.

So what is the difference between an enable secret and an enable password? While both provide the same overall functionality (authorizing users into a higher privilege level), how the Cisco IOS XE device stores the key is different. The key associated with the **enable password** is stored using a weak cipher (if the **service password-encryption** feature is enabled) or in clear text. It uses the Vigenere cipher which can be easily deciphered. The **enable secret** key uses MD5 for one-way password hashing which cannot be reversed. If someone has the hash, they will be unable to put this through a mathmatical formula to reverse it to clear text. It is susceptiable to dictionary attacks, but this is only if your Cisco IOS XE's configuration file has been compromised (see the recommendation above about re-issuing local secrets, passphrases, and keys).

If you have any network devices still configured with an enable password instead of an enable secret, it is strongly recommended to configure an enable secret (with a **different** key than the enable password) and remove the enable password. This is one of Cisco's recommended steps to remediate this authentication bypass vulnerability. It can be accomplished as simply as:

```
Router#config t
Enter configuration commands, one per line.  End with CNTL/Z.
Router(config)#enable secret F@ncy3nable5ecret
Router(config)#no enable password
Router(config)#
```

### Configure Netconf and Restconf Service-Level ACL's

There are most likely a very small number of sources that should be interfacing with the Netconf or Restconf services on your Cisco IOS XE devices. Once enabled, the default Netconf/Restconf configuration allows _any_ source to communicate with the Netconf/Restconf service, as long as it has IP reachability to your network device. To limit your exposure, you can configure [Netconf/Restconf service-level ACL's](https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/prog/configuration/1611/b_1611_programmability_cg/service_level_ACLs_NETCONF_RESTCONF.html) to restrict only known trusted source IP address ranges to communicate with these services on the network device. Although this is not guaranteed to secure your device (a compromised network management system may be within the permitted source address ranges), it is one method that can be used to make it far more difficult for an attacker.

To configure a service-level ACL and apply it to the Netconf and Restconf protocols, see the following as an example. In this case we are permitting two network management IP address ranges 10.1.255.0/24 and 10.2.255.0/24, followed by applying the ACL to the Netconf and Restconf processes:

```
Router#config t
Router(config)#ip access-list standard NET_MGMT_RANGES_ACL
Router(config-std-nacl)#permit 10.1.255.0 0.0.0.255
Router(config-std-nacl)#permit 10.2.255.0 0.0.0.255
Router(config-std-nacl)#exit
Router(config)#netconf-yang ssh ipv4 access-list name NET_MGMT_RANGES_ACL
Router(config)#restconf ipv4 access-list name NET_MGMT_RANGES_ACL
```

### Compare Configuration for Signs of Manipulation

As stated previously, this particular vulnerability allows an attacker to manipulate the configuration of your network device. As a result, you should be looking for any signs of manipulation within that configuration. A few steps that you can take to identify unauthorized configuration changes:

- Compare your running _and_ startup configurations to a known 'gold standard' and review any deviations
- Review any TACACS or RADIUS logs. This may require going as far back in time as you have been running the vulnerable Cisco IOS XE version or affected features
- Review any syslog data for when configuration changes have been made. If you are logging at level 5 (notice) or higher, you can search your log data for **SYS-5-CONFIG_I**

### Upgrade to an Unaffected Cisco IOS XE Software Version

Finally, if you are unable to modify the configuration of your network device so that it is not running affected features, you can upgrade the software version to one which is not affected by this vulnerability. This would require intrusive changes as the network device is upgraded, and would require more planning and research to identify which version of software to move to.
