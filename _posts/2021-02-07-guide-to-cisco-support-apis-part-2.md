---
title: "A Guide to Cisco Support API's - Part 2 - EoX"
tags:
  - Cisco
  - API
  - Automation
  - Python
last_modified_at: 2021-02-09T05:56:00-07:00
---

The Cisco Support API's provide some very useful end-points that enable you
to gain efficiencies on managing your Cisco hardware and software inventory.
In this post I present the use of the End of Life (EoX) API that allows you to
identify end-of-life equipment within your environment. The code snippets below will be written in in Python and closely follows my [Cisco Support API Query Repo](https://github.com/brianyaklin/cisco-support-api-query) on GitHub. Feel free to clone the repo, I intend to include more API end-points in the near future.

For a more general overview of the Cisco Support API's refer to
[part 1]({% post_url 2021-02-01-guide-to-cisco-support-apis-part-1 %}) of this series.

## What is the EoX API and why use it?

End-of-life hardware and software in an environment can be a risk to any organization. A vendor who has declared a particular model of hardware or version
of software is no longer going to permit you to RMA that hardware if it fails and
they may decide to no longer create patches for software versions. This leaves
you susceptible to hardware failures which you can't easily replace, or dangerous
security risks in software that is not getting patched.

The Cisco EoX API allows you to quickly obtain end-of-life information, by passing to the API as URL parameters your Product ID's (PID's), serial numbers, or software
release strings. There are end-points for each of these as well as a more general
API end-point for querying for EoX information in a specified date range. You can
reference [Cisco's EoX API](https://developer.cisco.com/docs/support-apis/#!eox/features) documentation for complete details on their use.

Here are a few notes on my experience working with these API end-points so far:

- I find the Get EoX by Product ID's end-point to be the most useful. It allows you to query up to 20 PID's at a time which helps reduce the number of GET requests you send, which keeps you within your daily query limits
- Make sure that you deduplicate the PID's, Serial Numbers, or Software Release strings so you can be more efficient in your querying
- If you query the API end-points too quickly your requests will be blocked by Cisco's rate limiter. Always include a sleep function of at 0.5 seconds so that you don't overwhelm Cisco's API service

## Example: Get EoX by Product ID's

This example is going to provide an overview of querying Cisco's EoX API end-point [Get EoX by Product ID's](https://developer.cisco.com/docs/support-apis/#!eox/get-eox-by-product-ids). These details are pulled from my [Cisco Support API Query Repo](https://github.com/brianyaklin/cisco-support-api-query) which also includes an example.py to show an easy way of using my utility functions.

> Before you begin make sure that you have registered your application with [Cisco's API console](https://apiconsole.cisco.com/) and have a valid Client Key and Client Secret with a grant-type of client credentials. Cisco outlines [application registration](https://developer.cisco.com/docs/support-apis/#!application-registration/application-registration) in more detail if you need an overview

We will break this exampledown into a few steps:

1. Install required modules
2. Authenticate with Cisco's API service
3. Query the EoX API
4. Save the EoX records to a CSV file

### 1. Install Required Modules

The main Python module that we will be using to interact with Cisco's API's will be the [Requests](https://requests.readthedocs.io/en/master/user/quickstart/) package. This module is easy to use and I believe wraps the lower-layer urllib3 module. Requests allows you to send various HTTP requests (POST, GET, UPDATE, DELETE, etc) as well as provide URL headers and parameters. Response data from API's like what Cisco offers often return data represented in XML or JSON, and the Requests module allows us to easily convert JSON data into a Python dictionary for our analysis. I will not be covering the Requests module in detail so I encourage you to explore the link above if you are curious.

Copy the [requirements.txt](https://github.com/brianyaklin/cisco-support-api-query/blob/main/requirements.txt) file from the repo and install the pacakges.
{% highlight shell %}
pip3 install -r requirements.txt
{% endhighlight %}

### 2. Authenticate with Cisco's API Service

Cisco's API's use token-based authentication when sending queries. This requires you to first authenticate against Cisco's API service using your client key and secret and if successful you will be provided with an authentication token which you can use in subsequent queries to Cisco API end-points that your application is registered for. The auth token that you are provided is good for 3600 seconds (60 minutes) which in all of my use-cases is more than sufficient.

My [api_login.py](https://github.com/brianyaklin/cisco-support-api-query/blob/main/util/api_login.py) script is more detailed, so this will be slimmed down version from the Python interpreter.

The following code is what we will work off of with a detailed explanation below.
{% highlight Python linenos %}
import time
import requests

class ApiLogin():
    def __init__(self, client_key: str, client_secret: str) -> None:
        self.client_key = client_key
        self.client_secret = client_secret
        self.login()

    def login(self) -> None:
        self.auth_token = None
        self.auth_start = time.time()
        SSO_URL = 'https://cloudsso.cisco.com/as/token.oauth2'

        params = {
            'grant_type': 'client_credentials',
            'client_id': self.client_key,
            'client_secret': self.client_secret,
        }

        req = requests.post(
            SSO_URL,
            params=params,
            timeout=10,
        )
        req.raise_for_status()

        self.auth_resp = req.json()

        self.auth_token = \
            f"{self.auth_resp['token_type']} {self.auth_resp['access_token']}"

    def auth_still_valid(self) -> None:
        if (time.time() - self.auth_start) >= (self.auth_resp['expires_in']):
            # Login again, which will set a self.url_headers with a new token
            self.login()
{% endhighlight %}

What we are doing here is creating a Python class called ApiLogin and its \__init__ function at line 5 requires two parameters; your client_key and client_secret. Upon instantiating a class and passing in client_key and client_secret arguments the `login()` function will immediately be called at line 8.

Once `login()` has been called it sets the current time with `self.auth_start = time.time()`. This will be later used to determine if our authentication token has expired.

To query the Cisco API login service we perform the following:
1. We set the URL to `https://cloudsso.cisco.com/as/token.oauth2` which is used for Cisco's API login service
2. The URL parameters are set in a Python dictionary called `params` at line 15 which sets the grant_type (we hard code this to `client_credentials`) along with our client key and client secret. Note that you have to use the keys `grant_type`, `client_id` and `client_secret`, as this is what Cisco's API login service requires
3. We are now ready to send our HTTP POST request using the Requests module at line 21. There are multiple arguments you can provide when using `requests.post()` but here we simply need to provide the URL to query and the URL parameters previously set
4. After sending the Post requests we test to confirm if the HTTP request was successful. This is accomplished using `req.raise_for_status()` which is a function the Requests module provides to us and it raises an HTTPError exception if an HTTP 4XX or 5XX response is received meaning that we either didn't authenticate correctly or the server experienced an issue. Here is an example of the complete authentication response (the access token is obfuscated for obvious reasons). You can see that you are given an access_token, token_type and expires_in values
```python
>>> api.auth_resp
{'access_token': 'AAABBBCCCDDDEEEFFFGGG', 'token_type': 'Bearer', 'expires_in': 3599}
```
5. If no error was received we can access the response data by assigning the JSON response to a python dictionary using the `resp.json()` function call. We assign this to our variable `self.auth_resp` for us to use at line 30 by assigning the `access_type` and `access_token` key values to `self.auth_token`.
6. Finally, a function called `auth_still_valid()` is defined which takese the compares the current time, `self.auth_start` and `self.auth_resp['expires_in']` to determine if the token has expired or not. If it has, it calles `login()` again to obtain a new token

So how would you use this class?
{% highlight Python %}
>>> from dotenv import dotenv_values
>>> from util.api_login import ApiLogin
>>> client_key = dotenv_values('.env')['CLIENT_KEY']
>>> client_secret = dotenv_values('.env')['CLIENT_SECRET']
>>> api = ApiLogin(client_key, client_secret)
>>> api.auth_token
'Bearer AAABBBCCCDDDEEEFFFGGG'
{% endhighlight%}

> Keep your API keys in a secure location just like you would any other username/password you use. These keys are associated with your Cisco CCO account. You should not expose your keys to your applications end users, you should not store these directly in your source code or version control, and instead should use environment variables or some other secure mechanism for storing and consuming your API keys (ex. AWS KMS). The above example uses Python's [dotenv module](https://github.com/theskumar/python-dotenv) which allows you to store environment variables in a file called .env. Ensure that your .gitignore file is configured to ignore this file.

The `api.auth_token` value is what will enable you to initiate subsequent queries against specific Cisco API end-points. The next section describes how we will use this and the response data for the EoX API end-point.

### 3. Query the EoX API

Once you have authenticated with Cisco's API service and have an authentication token you are now ready to query the EoX API end-point. We will be using the [Get EoX by Product ID's](https://developer.cisco.com/docs/support-apis/#!eox/get-eox-by-product-ids) end-point which allows us to query based on a product ID.

This example does not cover how you would obtain all of your product ID's from your entire infrastructure, but I have used a few methods to do so in the past:
- Use Python modules such as [netmiko](https://ktbyers.github.io/netmiko/) and [ntc-templates](https://github.com/networktocode/ntc-templates) to obtain the output of a "show version" and parse it into a Python dictionary with the product ID's and serial numbers
- Use [PySNMP](https://github.com/etingof/pysnmp) to query a devices [entPhysicalEntry](https://snmp.cloudapps.cisco.com/Support/SNMP/do/BrowseOID.do?local=en&translate=Translate&objectInput=1.3.6.1.2.1.47.1.1.1.1) table which will contain an assortment of valuable information including your PID's and serial numbers for each
- Use any other source of information that you have available that describes your inventory and can provide PID's

> It is important to note that you should identify EoX information not only on your chassis PID but on all other pieces of hardware that are installed in your device. This includes modules, fans, power supplies, transceivers, etc

My [api_eox.py](https://github.com/brianyaklin/cisco-support-api-query/blob/main/util/api_eox.py) script provides a mechanism to query Cisco's Get EoX by Product ID's API end-point, the code is as shown below:

{% highlight Python linenos %}
from typing import List
from typing import Dict
import time
import requests

class ApiEox():
    def __init__(self, auth_token: str, mime_type: str = 'application/json') -> None:
        self.url_headers = {
            'Accept': mime_type,
            'Authorization': auth_token,
        }
        self.items = []
        self.records = []

    def __send_query(self, url: str,) -> Dict:
        req = requests.get(
            url,
            headers=self.url_headers,
            timeout=10,
        )
        req.raise_for_status()
        return req.json()

    def query_by_pid(self, pids: List[str]) -> None:
        BLACK_LIST = ['', 'n/a', 'b', 'p', '^mf', 'unknown',
                      'unspecified', 'x']
        MAX_ITEMS = 20
        self.items = list({pid for pid in pids if pid.lower() not in BLACK_LIST})
        API_URL = 'https://api.cisco.com/supporttools/eox/rest/5/EOXByProductID/{}/{}'

        start_index = 0
        end_index = MAX_ITEMS
        while start_index <= len(self.items) - 1:
            page_index = 1
            pagination = True
            while pagination:
                url = API_URL.format(
                    page_index,
                    (',').join(self.items[start_index:end_index])
                )
                resp = self.__send_query(url)

                if resp.get('EOXRecord'):
                    self.records = self.records + resp['EOXRecord']

                if page_index >= resp['PaginationResponseRecord']['LastIndex']:
                    pagination = False
                else:
                    page_index += 1

                # Play nice with Cisco API's and rate limit your queries
                time.sleep(0.5)

            start_index = end_index
            end_index += MAX_ITEMS
{% endhighlight %}

This code creates a class named `ApiEox()` which allows us to query the EoX API multiple times and store the returned records in `self.records` for future reference.
It includes a few other tricks like blacklisting certain PID's, deduplicating the list of PID's and controlling pagination of the returned records and reading the.

Looking at the code in more detail we see:
1. The `\__init__` function accepts our auth_token we received in our ApiLogin() class, a MIME Type (we default by setting this to application/json but you can also use XML). These parameters are stored in the `self.url_headers` dictionary which will be used as part of our Requests.GET call later on
2. At lines 12 and 13 we declare `self.items` which will be used to store the list of PID's, and `self.records` which will store the returned EOXRecords that the API sends us
3. The `__send_query` function is an internal class function that controls sending the HTTP request and returns the response. The details of this is covered in more detail in step 2 above for logging in to the Cisco API service
4. The bulk of our code is handled in the `query_by_pid()` function at line 23 which accepts a single parameter; a list of PID's
5. I have defined a BLACK_LIST which is a list of unacceptable PID's at line 24. Based on experience in how I have gathered inventory data from parsing "show version" or querying for the SNMP table of entPhysicalEntry there tends to be a few values returned in the PID column that are irrelevant
6. At line 28 I use a [Python set comprehension](https://medium.com/swlh/set-comprehension-in-python3-for-beginners-80561a9b4007) which assigns the PID's to our previously declared `self.items` variable list and performs two things for me:
    1. It deduplicates the list of PID's that were provided, so we don't query Cisco's API for the same item twice (ex. you may have multiple Cisco ISR4321/K9, so why query for the same information more than once)
    2. I am able to compare each PID against my BLACK_LIST variable and discard it if its in the list
7. We declare the API_URL for the Get EoX by Product ID at line 29
8. Because you can query up to a maximum of 20 PID's in a single HTTP GET request to the API by comma seperating the PID's in the URL you are calling I accomplish this by:
    1. Declaring a `start_index` of 0 and `end_index` of our MAX_ITEMS (in this case 20) at lines 31 and 32
    2. I then loop through all items for as long as our `start_index` is less than the length of our `self.items - 1`. We subtract 1 because Python lists are zero-indexed
    3. I then define the URL to use in the query by doing a Python `join()` at lines 37 through 40. This `join()` statement will join together the PID's between the list indexes from the start_index up to the end_index (or to the end of the list if there aren't 20 items left), using a comma as a delimiter
    4. Skipping down a few lines past the query and response details (discussed in another bullet below) I now increment my start_index and end_index values at lines 54 and 55 so that the next query, if necessary, will include the items in `self.items` from indexes 20 through 39
9. At line 40 I call our private function `__send_query` with the URL as an argument and assign the response to the `resp` variable
10. A response from the Get EoX by Product ID API end-point is a JSON with keys ([full API details here](https://developer.cisco.com/docs/support-apis/#!eox/get-eox-by-product-ids)) describing the PaginationResponseRecord and the EOXRecord (which can contain multiple records, for all of the PID's you sent in the URL)
11. If an `EOXRecord` exists in the response I extend our `self.records` list to include the new records in line 43
12. We previously defined a page_index of 1 at line 34, but now we will review the PaginationResponseRecord to see if there is more than one page describing all of the records by looking at the LastIndex key at line 46. If there are multiple pages, we need to increment our page_index by one and query again. The while loop at line 36 will continue querying until our page_index value is the same as the LastIndex in the response and will then exit the loop
13. Because Cisco's API's only allow so many queries per second and per minute I include a sleep function with `time.sleep(0.5)` at line 52

So tying this all together we can use this code as follows:
{% highlight Python %}
>>> from util.api_eox import ApiEox
>>> eox = ApiEox(api.auth_token)
>>> pids = ['WS-C3750X-48PF-S', 'C3KX-PWR-1100WAC', ]
>>> eox.query_by_pid(pids)
{% endhighlight %}

We have now queries the API to get EoX information for two PID's. This information is stored in the `eox.records` class instance variable and is a list with two records:
{% highlight Python %}
>>> len(eox.records)
2
{% endhighlight %}

Each record is Python dictionary and has the following keys describing the record:
{% highlight Python %}
>>> eox.records[0].keys()
dict_keys(['EOLProductID', 'ProductIDDescription', 'ProductBulletinNumber', 'LinkToProductBulletinURL', 'EOXExternalAnnouncementDate', 'EndOfSaleDate', 'EndOfSWMaintenanceReleases', 'EndOfSecurityVulSupportDate', 'EndOfRoutineFailureAnalysisDate', 'EndOfServiceContractRenewal', 'LastDateOfSupport', 'EndOfSvcAttachDate', 'UpdatedTimeStamp', 'EOXMigrationDetails', 'EOXInputType', 'EOXInputValue'])
{% endhighlight %}

A more detailed look at the first record shows that the Product ID of WS-C3750X-48PF-S went end of sale on 2016-10-30 and its last date of support was 2021-10-31
{% highlight Python %}
>>> eox.records[0]['EndOfSaleDate']
{'value': '2016-10-30', 'dateFormat': 'YYYY-MM-DD'}
>>> eox.records[0]['LastDateOfSupport']
{'value': '2021-10-31', 'dateFormat': 'YYYY-MM-DD'}
{% endhighlight %}

### 4. Save the EoX records to a CSV file

So you now have the EoX records for all of the hardware within your environment stored in a Python dictionary. You will more than likely need to report on this to those responsible for financial planning, forecasting and coordination of replacing EoX equipment.
A simple method would be to save these records to a CSV file which I will show below, but you could get even more advanced by having a report that links each record back to the actual network inventory on a device by device basis.

The code to do a simple export to CSV is as follows
{% highlight Python linenos %}
import csv

#...previous code for logging into the API and obtaining EoX records

FNAME = 'eox_report.csv'
with open(FNAME, mode='w') as fhand:
    writer = csv.writer(fhand, delimiter=',', quotechar='"',
                        quoting=csv.QUOTE_MINIMAL)
    writer.writerow(['EOLProductID',
                        'ProductIDDescription',
                        'LastDateOfSupport',
                        'EndOfSWMaintenanceReleases',
                        'EOXExternalAnnouncementDate',
                        'EndOfSaleDate',
                        'EndOfSecurityVulSupportDate',
                        'EndOfRoutineFailureAnalysisDate',
                        'EndOfServiceContractRenewal',
                        'EndOfSvcAttachDate',
                        'LinkToProductBulletinURL', ])
    for record in eox.records:
        writer.writerow([record['EOLProductID'],
                            record['ProductIDDescription'],
                            record['LastDateOfSupport']['value'],
                            record['EndOfSWMaintenanceReleases']['value'],
                            record['EOXExternalAnnouncementDate']['value'],
                            record['EndOfSaleDate']['value'],
                            record['EndOfSecurityVulSupportDate']['value'],
                            record['EndOfRoutineFailureAnalysisDate']['value'],
                            record['EndOfServiceContractRenewal']['value'],
                            record['EndOfSvcAttachDate']['value'],
                            record['LinkToProductBulletinURL'], ])

print(f'EOX records written to file {FNAME}')
{% endhighlight %}

This code uses the Python CSV's writer() function to loop through each record in eox.records and saves the contents of each record as a new row in that CSV file.

## Conclusion

Using Cisco's EoX API can help you and your customers by easily identifying which hardware is, or may soon become, end-of-life. You can transform the data in whichever way you wish to create powerful reports!

## A note on the Get EoX by Software Release Strings API end-point

The Get EoX by Software Release Strings end-point was trickier to work with because it requires you to enter your software versions using a [SWReleaseStringType](https://developer.cisco.com/docs/support-apis/#eox/SWReleaseStringType). This requires you to create a string representing the software version and type together such as "input1=12.4(15),IOS&input2=16.3.9,IOS-XE". Depending on how you have transformed your data, this can be more difficult to programmatically create this URL query string.

The other difficulty I had in working with this API end-point is I believed it would return end-of-life details on the software versions themselves. Instead, it returned EoX information using a PID as a key such as "S280IPBK9-12424T=" which is a representation of running 12.4(24)T on a Cisco 2801 IOS IP Base router. I would have found this much more useful if it returned these as two separate PID's; one indicating 12.4(24)T and another as CISCO2801 so I could more easily compare this against my hardware and software inventory. If anyone has identified a way to use this other PID I would enjoy hearing how they have compared this with their inventory.
