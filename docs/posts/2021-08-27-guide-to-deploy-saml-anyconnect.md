---
date:
  created: 2021-08-27
tags:
  - Security
  - Cisco
  - SAML
---

# A Practical Guide to Deploying SAML for AnyConnect (External)

The pandemic has rapidly advanced the need for high-quality and secure remote access VPN solutions (RAVPN). As a result, many RAVPN solutions provided by vendors have been targetted by hackers. This has resulted in newly identified vulnerabilities and security advisories being released by the vendors. One area of concern is around user credential management and multi-factor authentication (MFA). The configuration examples, provided by Cisco and authentication providers, for configuring SAML and Cisco AnyConnect fail to highlight how to configure multiple group-policies so that you can restrict access appropriately for each business unit and vendor. Instead, they highlight have to apply a single group-policy to cover all of your remote access users. I've written a blog post for my employer Optanix that provides a production-grade example of how to deploy SAML for Cisco AnyConnect, using multiple group-policies and LDAP attribute maps for fine-grained access control.

Read [A Practical Guide to Deploying SAML for AnyConnect](https://www.optanix.com/practical-guide-deploying-saml-anyconnect/) for more details and let me know what you think!
