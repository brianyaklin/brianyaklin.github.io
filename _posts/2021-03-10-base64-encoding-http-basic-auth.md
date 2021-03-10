---
title: "Base64 Encoding with HTTP Basic Auth for API's"
tags:
  - Cisco
  - Python
---

I have been exploring the [Cisco DNA Center REST API](https://developer.cisco.com/docs/dna-center/#!cisco-dna-2-1-2-x-api-overview) as part of studying for the [Cisco Certified DevNet Associate](https://developer.cisco.com/certification/devnet-associate/) certification exam. Today while reading through the official certification guide it talked about how authorization into the API required that your credentials be passed as a base64 encoded string, but it didn't indicate how to accomplish this.

For those that aren't familiar with [Cisco's DevNet Sandboxes](https://devnetsandbox.cisco.com/RM/Topology), Cisco provides **free** access to read-only always-on and reservation based sandbox environments. These environments permit a developer access to a wide variety of technologies that Cisco customers deploy, including ACI, ISE, FirePower FMC, Viptela vManage, StealthWatch, Umbrella, Webex Meetings, and many more. The one that I'm currently exploring is the Cisco DNA Center REST API. This article is going to briefly explain base64 encoding and how to use it for authorization with REST API's, specifically Cisco DNA Center. If you wanted to follow along, open up the Always-On sandbox for Cisco DNA Center AO 2.1.2.5.

## What is base64 encoding?

There are quite a few articles out there, but the one that I found on [Stack Abuse explained it](https://stackabuse.com/encoding-and-decoding-base64-strings-in-python/) quite well and simply enough. I encourage you to read the article to gain a better understand. The main highlights on base64:

- It's a conversion between bytes and ASCII characters
- There are 64 characters represented in total (26 Uppercase, 26 Lowercase, 10 numbers, and + and / characters)
- Important: base64 is not an encryption algorithm as it can be easily reversed, so should not be used for security purposes

## Using base64 with HTTP Basic Auth

I have talked briefly about HTTP Basic Auth in my guide to the [Cisco NFVIS API]({% post_url 2021-03-02-initial-thoughts-cisco-nfvis-api %}). It is an authentication scheme that includes your username and password in an HTTP 'Authentication' header. It is very important that when using Basic Auth that you use HTTPS, as the credentials are not encrypted in the HTTP headers. Security is dependent on HTTPS/TLS.

Base64 encoding for authentication with a REST API will take on a few different forms, depending on the REST API so check the documentation. The [Cisco DNA Center REST API documentation](https://developer.cisco.com/docs/dna-center/#!cisco-dna-2-1-2-x-api-overview) indicates that the usernamd and password should be represented as a string that is colon separated before being encoded as base64. In the case of Cisco's DevNet sandbox for DNA Center, that means the username and password would be:

```
devnetuser:Cisco123
```

> Other API's may require you to separate the username and password with a + sign or another character.

So how can you use this to authorize yourself against the DNA Center REST API? See the following steps using Pythons Request module.

First lets import the [base64 module](https://docs.python.org/3/library/base64.html) and convert our username and password into a base64 encoded byte string.

```python
>>> import base64
>>> auth_str = 'devnetuser:Cisco123!'
>>> byte_str = auth_str.encode('ascii')
>>> byte_str
b'devnetuser:Cisco123!'
>>> auth_b64 = base64.b64encode(byte_str)
>>> auth_b64
b'ZGV2bmV0dXNlcjpDaXNjbzEyMyE='
```

You can see above that we can create a byte string using the `.encode('ascii')` function on our auth_str object. We need to do this because the base64.b64encode() function requires a bytes-like object. We then create an auth_b64 byte string which is now our username and password encoded the way the REST API will require it. If you are using another tool like cURL or Postman to test REST API's, you can take this string and set it in your HTTP headers. The rest of this article focuses on using it with Pythons Request module.

To authenticate with the DNA Center REST API we need to send a POST request to `/dna/system/api/v1/auth/token` with an Authorization and Content-Type HTTP header, and if we successfully authenticate we will be returned an API token which we can use in subsequent API requests.

```python
>>> import requests
>>> headers = {
...     'Authorization': 'Basic {}'.format(auth_b64.decode()),
...     'Content-Type': 'application/json',
... }
>>> AUTH_URL = 'https://sandboxdnac.cisco.com/dna/system/api/v1/auth/token'
>>> resp = requests.post(AUTH_URL, headers=headers, timeout=20, verify=False)
>>> resp.status_code
200
```

In the above commands we imported the Requests package and set our HTTP headers with an Authorization header and Content-Type header that specifies we want to have data returned in JSON format. Not that for the Authorization header we actually need to perform a `decode()` on the byte string we previously created so that it is represented as a Python string object. This ensures that the REST API likes the data we send it. Finally, we send an HTTP POST request to the AUTH_URL and add our headers to the request. If you successfully authenticated you will see a response status code of 200/OK.

The data that the REST API returns to us is actually a JSON response containing the authorization token we can use in subsequent API requests:

```python
>>> resp_data = resp.json()
>>> resp_data.keys()
dict_keys(['Token'])
>>> resp_data['Token']
'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2MDJjMGUyODE0NzEwYTIyZDFmN2UxNzIiLCJhdXRoU291cmNlIjoiaW50ZXJuYWwiLCJ0ZW5hbnROYW1lIjoiVE5UMCIsInJvbGVzIjpbIjYwMmJlYmU1MTQ3MTBhMDBjOThmYTQwOSJdLCJ0ZW5hbnRJZCI6IjYwMmJlYmU1MTQ3MTBhMDBjOThmYTQwMiIsImV4cCI6MTYxNTM4ODA4NCwiaWF0IjoxNjE1Mzg0NDg0LCJqdGkiOiI5MjI3MmQ5Mi1lODRjLTRmMTUtOTFhNy1lNDI3ZmYwNmQxMDgiLCJ1c2VybmFtZSI6ImRldm5ldHVzZXIifQ.ZyJAEvSsjKm7Re-uTnXN7kyVf_pYVHwrmLl9m3z39XEkWUncWQhjRYybhgkUjVolJM10oaL31miWXRefZA0DYjXD0bW7zta_5Lr9AyFV66stosDtpzC_80Frh_n5oVi4gR4lvFtqPWixTrSB4c4aJxF1TqkFMUX8q_HpyDC0pcIRVOtyjTKltcmG8USOQQhPEMLW6vdwP8JEfK7HJUPuj0cMpIlXALqJE_k-5qvxHbNWWiIIST99wPGKAAA35aN_02THNSTuRF_bm2Oxr4ScWuwou3TwKIajB5Bp4jg-sTboO5NzRnGhkq9ZcA_S0j22KgceD2W431e6q1f7wK4_7g'
>>>
```

This response token is actually a JSON Web Token (JWT) and if you plug it into the [debugger at jwt.io](https://jwt.io/) you can see some additional details. The benefits of using a token for authorization subsequent API calls are:

- They are stateless, meaning the server receiving the request can validate them immediately as they are signed with a public key
- They have an expiration date/time
- They can be revoked by the server if they are compromised
- They are signed, so they can't be tampered with

## A quicker way of using HTTP Basic Auth with Requests

The above example of importing the base64 module and converting the username/password was used to demonstrate base64 encoded strings for HTTP Basic Auth. The good news is the Python Requests module includes a shortcut for you by importing requests.auth.HTTPBasicAuth. This makes it far simpler to use as demonstrated in this example.

```python
>>> import requests
>>> from requests.auth import HTTPBasicAuth
>>> headers = {'Content-Type': 'application/json',}
>>> username = 'devnetuser'
>>> password = 'Cisco123!'
>>> AUTH_URL = 'https://sandboxdnac.cisco.com/dna/system/api/v1/auth/token'
>>> resp = requests.post(
...     AUTH_URL,
...     headers=headers,
...     timeout=20,
...     verify=False,
...     auth=HTTPBasicAuth(username, password))
>>> resp.status_code
200
>>> resp_data = resp.json()
>>> resp_data['Token']
'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2MDJjMGUyODE0NzEwYTIyZDFmN2UxNzIiLCJhdXRoU291cmNlIjoiaW50ZXJuYWwiLCJ0ZW5hbnROYW1lIjoiVE5UMCIsInJvbGVzIjpbIjYwMmJlYmU1MTQ3MTBhMDBjOThmYTQwOSJdLCJ0ZW5hbnRJZCI6IjYwMmJlYmU1MTQ3MTBhMDBjOThmYTQwMiIsImV4cCI6MTYxNTM4OTA2OCwiaWF0IjoxNjE1Mzg1NDY4LCJqdGkiOiJlMTI3ODRjZC1iOGYyLTRlMzQtOGRhOS01ZWJkNTk5MTRlMTIiLCJ1c2VybmFtZSI6ImRldm5ldHVzZXIifQ.kKOBqO-eBJTDqK7t3heN057wVQLMTzGGbPn1vL4SQcvMsd2LLQ6CBn2Mr1QPgluit11gzjx3wM7FOLRJILBbZhhbSxSDymfZoNu2CZzdtIy7yz53bDDHwWMf5m8ymqBrFfb-Si8W_vEaT5XTbyjAydWyMiWN4l7ddKH7PC6h6ZoFdI6ko3bFh8H3j3IvSG64dFQp5OLzrMWmKaxqr2OvdlJMo_bXKuuW1pBr8ifjuaPTs3dKhVjbsIrxeQ7fgmvHge5pvfmzPQqEFV-yNYR9fNwEZ8T3FyLKfD_O2NCPiiw5RsYqUWZQkvAT7kqvOeluLHvrTwn3sHvHvGqxhncs2Q'
>>>
```

## HTTP Basic Auth with Ansible URI Module

While I haven't use HTTP Basic Auth with [Ansible's URI module](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/uri_module.html), it appears to support this authentication mechanism by providing the url_password and url_username parameters. You potentially need to set the force_basic_auth parameter to True if the REST API you're working with doesn't send an HTTP 401 status code on an initial request.

And with that I'm hoping you have gained a better understanding of base64 encoding and HTTP Basic Auth with REST API's!
