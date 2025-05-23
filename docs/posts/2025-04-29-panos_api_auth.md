---
date:
  created: 2025-04-29
categories:
  - Programmability
tags:
  - Palo Alto
  - Automation
---

# Palo Alto PANOS API Authentication

In this article we will explore the various methods used for [authenticating](https://docs.paloaltonetworks.com/pan-os/10-2/pan-os-panorama-api/get-started-with-the-pan-os-xml-api/authenticate-your-api-requests) against Palo Alto's PANOS API which allows administrators to programmatically interface with Palo Alto firewalls and Panorama appliances. The methods discussed cover both the [XML](https://docs.paloaltonetworks.com/pan-os/10-2/pan-os-panorama-api/get-started-with-the-pan-os-xml-api) and [REST](https://docs.paloaltonetworks.com/pan-os/10-2/pan-os-panorama-api/get-started-with-the-pan-os-rest-api) API's. There are a few considerations to make when deciding how to configure your appliances to authenticate API requests as well as how to handle API authentication in code.

<!-- more -->

## API Authentication Configuration

### Minimum Required Configuration

The PANOS API requires, at a minimum, that a local administrator account exists with any of the Dynamic administrator types (e.g. superuser, device administrator, etc.). Other than in a lab environment it would not be recommended to use a local account that multiple administrators have access to, for authenticating requests of any form to your appliance. Accounts should always be attributable to a single user or function and given only the access that is necessary for that user/function. This is described in the subsequent section.

### Least Privileged Access with Admin Roles

Authenticating administrators to the API should be performed on a user/function basis. If you allow your administrators to use the API, you can configure the firewall [admin roles](https://docs.paloaltonetworks.com/pan-os/10-2/pan-os-admin/firewall-administration/manage-firewall-administrators/configure-an-admin-role-profile) to permit each role the specific level of access that is required. In situations where the API is used programmatically by an external service (e.g. a monitoring platform or some other automated system), it is beneficial to create admin roles for each external service. Each service often requires different levels of access and creating an admin role per service allows the necessary flexibility.

For administrator based admin roles (e.g. the roles that authenticate a human logging into the appliance), you can set specific options on the XML API and REST API tabs of the admin role. Unfortunately, the documentation is a bit light on explaining each option for the XML API privileges and you only have the option to enable or disable access. There is greater flexibility for the REST API, similar to how you authorize an administrator to the web UI.

For external service based admin roles (e.g. monitoring platforms), a good recommendation to follow is to disable all options across the various tabs of the admin role and then explicitly enable the options required for the external service. The account that an external service uses to programmatically access an appliance should never need to use the web UI. Although outside of the scope of this article, some external services still rely on CLI access and parsing CLI output instead of using API access. Consult the documentation associated with the external service or discuss with those who manage the code that interfaces with your appliances API.

### Authentication Profiles

Your devices authentication settings (Device > Setup > Management > Authentication Settings) allows you to configure an authentication profile for non-local admins. If using [SAML](https://docs.paloaltonetworks.com/pan-os/10-2/pan-os-admin/authentication/configure-saml-authentication) to authenticate administrators, starting in PANOS 10.2 you now how have the option to identify an authentication profile/sequence for non-UI access. It is [required](https://docs.paloaltonetworks.com/pan-os/10-2/pan-os-admin/authentication/configure-an-authentication-profile-and-sequence) to configure non-SAML based authentication for accessing the API (and CLI), as redirecting to your IdP login page is not possible for these types of requests.

If you're remotely authenticating logins with a method other than SAML, you only need to set the Authentication Profile at the above mentioned path (not the Authentication Profile Non-UI option).

### API Key Lifetime

A common recommendation is that API keys should be rotated every 30 to 90 days. Palo Alto sets a dangerous default of zero which effectively indicates keys never expire. To adjust API key lifetime browse to Device > Setup > Management > Authentication Settings and set the value for API Key Lifetime (values can be between 0 minutes, no expiration, and 525600 minutes which is 365 days).

You should reference your organization best practices when determining to API key lifetime. In some cases the guideline may fall under a more general guideline around user/system authentication.

In my opinion, there is no reason that the value shouldn't be similar to that of the standard Idle Timeout for administrator logins, especially if you allow administrators to access the API. If you must be in compliance with NIST or CIS, administrator login idle timeout values usually need to be 20 minutes or less. Although Palo Alto's Idle Timeout is detecting inactivity in an admin session, API key lifetime isn't measured between API calls, but from the point in time the key is generated regardless of how many API queries are made after that. What you may find is that some external platforms/products which use the API don't effectively check for API key duration and renew their API key when making a series of subsequent calls.

## Authentication Examples

### Obtaining an API key

The preferred method for authenticating against the PANOS API is to generate an API key. This ensures that the username and password is only passed once to the device and subsequent API queries pass the timebound API key which will expire (as long as you have properly set an API key lifetime) . To generate an API key can use the /api/$type=keygen URL path on your Palo Alto appliance.

!!! note
    If you're using special characters in the password, cURL may require that you use different options such as --data-urlencode for submitting form data. This will ensure that cURL interpret the special characters as part of the value associated with a form field and not part of the parametrization of the key/value pairs. In the below example the password has an & character which would fail when using the -d cURL flag but is successfully passed when using --data-urlencode. Python's Request module already URL encodes the data values, so no additional changes are required.

!!! warning
    Follow best practices when handling any form of credential/secret in code. The intent of this post is not meant to cover secure code practices, but to provide examples of working with the Palo Alto PANOS API.

=== "Python"
    The following shows using Python's Request package to send a POST request to the PANOS API to generate a new API key.
    ```py linenums="1" hl_lines="17-25"
    --8<-- "snippets/panos_api_auth.py"
    ```
=== "cURL"
    ```text
    curl -k -H "Content-Type: application/x-www-form-urlencoded" \
    -X POST 'https://192.168.12.50/api/?type=keygen' \
    -d 'user=apiuser&password=JNn0Sg444s7D0jy5'
    ```
=== "cURL with special character password"
    ```text
    curl -k -H "Content-Type: application/x-www-form-urlencoded" \
    -X POST 'https://192.168.12.50/api/?type=keygen' \
    -d 'user=apiuser' \
    --data-urlencode 'password=JNn0Sg444s7D0jy5&'
    ```

A successfully authenticated call to the API keygen path results in an XML response that includes the API key:
```xml title="XML response with API key"
<response status = 'success'>
  <result>
    <key>LUFRPT0xTFE0dHZzVEVMYUV4dlNuUi9GeFFjeVl4cE09R25NSVgyYysyVEw4VmZRakdTazc2cjFKK05HRGhoVXIvRGFYN1lFMHlRUXVwaXhNNjRsTitDNWNaL2pWWjNPbzk5NXhzRGtsQy92NnRudjRyeDh0K3c9PQ==</key>
  </result>
</response>
```

### Using the API key in subsequent API calls
Now that you have an API key you can use it in subsequent API calls. This example shows running an operational command on the device.
=== "Python"
    ```py linenums="1" hl_lines="27-44"
    --8<-- "snippets/panos_api_auth.py"
    ```
=== "cURL"
    ```text
    curl -k -H "X-PAN-KEY: LUFRPT1Hd3dCOC80S3hqd1lMU01lbnBpOEN1MENkbEU9R25NSVgyYysyVEw4VmZRakdTazc2bnZNZnplcTdxVmpabGNTRnY3cENLNEEzaFpBbDM3N21xYlFYRjdJOFZOWDk1ajNTVTgrUGFlWU1PRmkvLzdtMFE9PQ==" \
    -G 'https://192.168.12.50/api/' \
    -d type=op \
    -d cmd='<show><system><info></info></system></show>'
    ```

The XML response to the API query for the operational command of 'show system info' would look like the following:
```xml
<response status="success">
  <result>
    <system>
      <hostname>PA-LAB</hostname>
      <ip-address>192.168.12.50</ip-address>
      <public-ip-address>unknown</public-ip-address>
      <netmask>255.255.255.0</netmask>
      <default-gateway>192.168.12.1</default-gateway>
      <is-dhcp>no</is-dhcp>
      <ipv6-address>unknown</ipv6-address>
      <ipv6-link-local-address>fe80::8e36:7aff:fe02:418e/64</ipv6-link-local-address>
      <mac-address>8c:36:7a:02:41:8e</mac-address>
      <time>Wed Apr 30 15:14:34 2025</time>
      <uptime>65 days, 8:44:39</uptime>
      <devicename>PA-LAB</devicename>
      <family>#########</family>
      <model>#########</model>
      <serial>#########</serial>
      <cloud-mode>non-cloud</cloud-mode>
      <sw-version>10.2.11-h12</sw-version>
      <global-protect-client-package-version>0.0.0</global-protect-client-package-version>
      <device-dictionary-version>172-597</device-dictionary-version>
      <device-dictionary-release-date>2025/04/25 12:16:03 MDT</device-dictionary-release-date>
      <app-version>8971-9419</app-version>
      <app-release-date>2025/04/28 16:06:06 MDT</app-release-date>
      <av-version>5169-5689</av-version>
      <av-release-date>2025/04/29 05:00:05 MDT</av-release-date>
      <threat-version>8971-9419</threat-version>
      <threat-release-date>2025/04/28 16:06:06 MDT</threat-release-date>
      <wf-private-version>0</wf-private-version>
      <wf-private-release-date>unknown</wf-private-release-date>
      <url-db>paloaltonetworks</url-db>
      <wildfire-version>955464-959418</wildfire-version>
      <wildfire-release-date>2025/02/24 07:42:12 MST</wildfire-release-date>
      <wildfire-rt>Disabled</wildfire-rt>
      <url-filtering-version>20250430.20332</url-filtering-version>
      <global-protect-datafile-version>unknown</global-protect-datafile-version>
      <global-protect-datafile-release-date>unknown</global-protect-datafile-release-date>
      <global-protect-clientless-vpn-version>0</global-protect-clientless-vpn-version>
      <logdb-version>10.2.1</logdb-version>
      <plugin_versions>
        <entry name='dlp' version='3.0.9'>
          <pkginfo>dlp-3.0.9</pkginfo>
        </entry>
      </plugin_versions>
      <platform-family>400</platform-family>
      <vpn-disable-mode>off</vpn-disable-mode>
      <multi-vsys>off</multi-vsys>
      <ZTP>Disabled</ZTP>
      <operational-mode>normal</operational-mode>
      <advanced-routing>off</advanced-routing>
      <device-certificate-status>Valid</device-certificate-status>
    </system>
  </result>
</response>
```
### Alternative Authentication Method
!!! warning
    I would discourage using the method mentioned in this section. The point of covering this is to highlight the method that Palo Alto encourages people to use, and to discuss the reasons for not using this method.

Alternatively, Palo Alto [encourages](https://docs.paloaltonetworks.com/pan-os/10-2/pan-os-panorama-api/get-started-with-the-pan-os-xml-api/authenticate-your-api-requests) you to use HTTP basic auth to authenticate API requests. They make no mention of using the API key that was [previously obtained](https://docs.paloaltonetworks.com/pan-os/10-2/pan-os-panorama-api/get-started-with-the-pan-os-xml-api/get-your-api-key). Generally speaking, basic auth should be discouraged as you are continually passing the username and password in every HTTP request in clear text. Basic auth only base 64 encodes the username and password and is easily reversable (decoded).

=== "Python"
    ```py linenums="1"
    --8<-- "snippets/panos_api_auth_basic.py"
    ```
=== "cURL"
    ```text
    curl -k -G 'https://192.168.12.50/api/' \
    -d type=op \
    -d cmd='<show><system><info></info></system></show>' \
    -u "apiuser:JNn0Sg444s7D0jy5&"
    ```

As you can see in the above examples, the username and password are passed in each API query which makes it more susceptible to compromise. Instead, using the username and password to get an API key which is used in subsequent API queries ensures that the username/password are only used once.

## Additional Notes on API Authentication

### Expiring API Keys

Palo Alto provides a mechanism to expire all API keys. Unfortunately this can't be controlled on a key by key basis. Browse to Device > Setup > Management > Authentication Settings and click the Expire All API Keys link.

It's not obvious how changing the API key lifetime affects existing API keys. If you allow a long API key lifetime duration or used the default of zero (API keys never expire) and then adjust the lifetime to a lower duration, I would recommend expiring all keys after you have made the change.

Also note that subsequent API key generation calls will immediately expire previous API keys associated with the account.

### Palo Alto PANOS API Key Weaknesses

!!! warning
    The following details provide steps that show how the API key can be decoded and decrypted, resulting in the original username/password used to create the API key being returned. Do not submit production API keys to public sites. If you intend to test this out, only submit an API key used in a lab that you intend to rotate immediately after.

    If you're curious as to how the decryption is performed and how the following site is handling data you submit in the form, feel free to review the Github repo for [panos-crypto-tools](https://github.com/Nothing4You/panos-crypto-tools). Note that as of the writing of this post, decryption of the API key is done locally in your browser, no data is submitted to an external site. However, always validate beforehand.

Although it is not documented on Palo Alto's site, it is well known that Palo Alto PANOS API keys contain the username/password that was used to create the API key in the first place. Although the API key is encrypted, its encrypted using the appliances [master key](https://docs.paloaltonetworks.com/pan-os/10-2/pan-os-admin/certificate-management/configure-the-master-key). To make matters worse, very few organizations manage their master key effectively and often leave it set to the default value which is also well known. If a non-default master key is used but becomes compromised, your API keys can also be decrypted.

To reverse a PANOS API key you first need to base64decode the key.

```py
import base64
key = 'LUFRPT1Hd3dCOC80S3hqd1lMU01lbnBpOEN1MENkbEU9R25NSVgyYysyVEw4VmZRakdTazc2bnZNZnplcTdxVmpabGNTRnY3cENLNEEzaFpBbDM3N21xYlFYRjdJOFZOWDk1ajNTVTgrUGFlWU1PRmkvLzdtMFE9PQ=='
base64.b64decode(key)
```

The above Python code results in the following string being returned.
```py
b'-AQ==GwwB8/4KxjwYLSMenpi8Cu0CdlE=GnMIX2c+2TL8VfQjGSk76nvMfzeq7qVjZlcSFv7pCK4A3hZAl377mqbQXF7I8VNX95j3SU8+PaeYMOFi//7m0Q=='
```

If you take the string contained between the single quotes to the [PANOS Crypto Tools](https://nothing4you.github.io/panos-crypto-tools/) site, you can decrypt the string further and see that it returns the username and password you have seen in previous examples within this post.

## Subsequent API Query Authentication Behaviour

When using an API key across multiple API queries, its important to note that the username and password thats encrypted and encoded within the API key is authenticated for each request. Deleting an admin account or changing its password will render the API key ineffective.

!!! note
    If admins are remotely authenticated (e.g. using RADIUS) and use a pin+token based password, such as with RSA, any API query after obtaining the API key will fail due to the single-user nature of this type of authentication method. To make subsequent API calls with this type of authentication method refer to the Persistent API Sessions section below.

To observe the behaviour, the first step is to generate the API key:

```xml
curl -k -H "Content-Type: application/x-www-form-urlencoded" \
-X POST 'https://192.168.12.50/api/?type=keygen' \
-d 'user=apiuser' \
--data-urlencode 'password=JNn0Sg444s7D0jy5&'
<response status = 'success'><result><key>LUFRPT1IanVrY0k4aUFtUURsaks0MmZ5T2VxNytUckE9R25NSVgyYysyVEw4VmZRakdTazc2bnZNZnplcTdxVmpabGNTRnY3cENLNUl5ZXB4ZDhUVkNJR0Y4VTdXS2pRdFhtU2tPMnp5MEdKejgzTGJsbnpsRmc9PQ==</key></result></response>
```

Confirm that you're able to query the API using the key:

```xml
curl -k -H "X-PAN-KEY: LUFRPT1IanVrY0k4aUFtUURsaks0MmZ5T2VxNytUckE9R25NSVgyYysyVEw4VmZRakdTazc2bnZNZnplcTdxVmpabGNTRnY3cENLNUl5ZXB4ZDhUVkNJR0Y4VTdXS2pRdFhtU2tPMnp5MEdKejgzTGJsbnpsRmc9PQ==" \
-G 'https://192.168.12.50/api/' \
-d type=op \
-d cmd='<show><system><info></info></system></show>'
<response status="success"><result>...Removed for brevity...</result></response>
```

Then change the password associated with the apiuser account (there isn't a method to disable an account). Query the API again and you'll see that an HTTP 403 error is returned:

```xml
curl -k -H "X-PAN-KEY: LUFRPT1IanVrY0k4aUFtUURsaks0MmZ5T2VxNytUckE9R25NSVgyYysyVEw4VmZRakdTazc2bnZNZnplcTdxVmpabGNTRnY3cENLNUl5ZXB4ZDhUVkNJR0Y4VTdXS2pRdFhtU2tPMnp5MEdKejgzTGJsbnpsRmc9PQ==" \
-G 'https://192.168.12.50/api/' \
-d type=op \
-d cmd='<show><system><info></info></system></show>'
<response status = 'error' code = '403'><result><msg>Invalid Credential</msg></result></response>
```

Finally, set the password associated with the apiuser account back to the original password that you used to obtain the API key. Query the API again and you'll see that a successful response is returned:

```xml
curl -k -H "X-PAN-KEY: LUFRPT1IanVrY0k4aUFtUURsaks0MmZ5T2VxNytUckE9R25NSVgyYysyVEw4VmZRakdTazc2bnZNZnplcTdxVmpabGNTRnY3cENLNUl5ZXB4ZDhUVkNJR0Y4VTdXS2pRdFhtU2tPMnp5MEdKejgzTGJsbnpsRmc9PQ==" \
-G 'https://192.168.12.50/api/' \
-d type=op \
-d cmd='<show><system><info></info></system></show>'
<response status="success"><result>...Removed for brevity...</result></response>
```

## Persistent API Sessions

As mentioned in the above section, if using a remote authentication method that leverages single-use passwords (e.g. pin+token), subsequent API calls will fail in the Python and cURL methods shown so far in this post. However, you can create a [Python Requests session object](https://requests.readthedocs.io/en/latest/user/advanced/#session-objects) to maintain a persistent HTTP session which allows you to send multiple API queries.

=== "Python"
    ```py linenums="1" hl_lines="18 19 39 47"
    --8<-- "snippets/panos_api_auth_session.py"
    ```