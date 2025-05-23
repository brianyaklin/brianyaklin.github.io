---
date:
  created: 2021-02-01
categories:
  - Programmability
tags:
  - Cisco
  - API
  - Automation
---

# A Guide to Cisco Support API's - Part 1

Managing your network infrastructure hardware, software and maintenance
lifecycle workflow tends to be a painful process. It means gathering large
amounts of telemetry from your network devices, transforming that data into
a format (excel, csv, etc) that you can use to compare, update, and track
and then determine the actions you need to take. A year later you get to
wash-rinse-repeate the whole process over again. If you are fortunate
enough to have a configuration management database (CMDB), this becomes
easier, but often these applications require some level of manual effort
to keep up-to-date. They can also cost you financially, sometimes more than
you are willing or able to pay.

<!-- more -->

In come [Cisco's Support API's](https://developer.cisco.com/site/support-apis/),
enabling you to take over the reins and have a little more flexibility in how
you manage your Cisco inventory. In part 1 of this series of posts I provide an
overview of how you can use these API's on your own or your customers networks.
Part 2 of this series looks to provide a few Python snippets showing how to
interact with the API's. For a detailed guide, refer to
[Cisco's Support API Docs](https://developer.cisco.com/docs/support-apis/#!introduction-to-cisco-support-apis).

!!! Note
    Cisco Support API's enable you to be flexible and agile on what you want to report while also considering **your** business context that other off-the-shelf applications are unable to comprehend.

## Cisco Support API Use-Cases

Before going into detail on the API's, its useful to understand why you might want
to use them in the first place. I have been using these API's for a number of reasons
including:

- Hardware life-cycle planning
- Reporting for Cisco maintenance renewals
- Bug scrubs on existing and future software versions
- Identifying recommended software versions

!!! Note
    Automating reporting and analysis tasks allows you to provide low level-of-effort (LoE) high-value services to your customers on a more frequent and recurring basis.

Yes, all of these tasks can be done manually but when you need to do this at scale
across multiple large environments with a wide variety of hardware models and
software versions in use, doing so manually becomes very time consuming. These API's
have allowed me to provide low LoE value-add services to my customers
by decreasing the amount of time spent preparing a recommendation which a customer may
or may not be able to move foward with. The customer gets a nice detailed report that
they can use in the future and there is a chance that I may get a rewarding project
from them to perform a hardware or software life-cycle across their environment. No
matter the outcome, your relationship with your customers will be enhanced by
providing them with this information.

## Cisco Support API Introduction

For Cisco customers with Smart Net Total Care (SNTC) or partners with Partner
Support Services (PSS), gaining access to Cisco's Support API's is as simple as
registering your application/script on [Cisco's API console](https://apiconsole.cisco.com/).
There are currently eight API end-points that you are able to interface with:

- Automated Software Distribution
- Bug
- Case
- EoX
- Product Information
- Serial Number to Information
- Service Order Return (RMA)
- Software Suggestion

When you register an application you pick which of the above API end-points you would
like to associate with the application. If you have multiple applications or
scripts you are developing it might be beneficial to create an unique
application in the API console for each. Each application you register will
have rate limits applied to each (ex. 10 calls per second, 5000 calls per day)
Creating multiple applications in the API console for each application you
are developing helps ensure you have the necessary resources for each.

You will also need to pick an authentication credential type that your
application will use to login to the API console. Cisco uses OAuth2.0
credentials and has four grant types available. I personally use the
`Client Credentials` grant type which provides you with a Client ID and Client Secret.
Think of these as your username and password. These will be used to authenticate
you against the API console and will provide back an access token for you to
query each API end-point. More detail on the authentication workflow will be found
in Part 2 of this series.

!!! Warning
    **Keep your keys in a secure location** just like you would any other username/password you use. These keys are associated with **your** Cisco CCO account. You should not expose your keys to your applications end users, you should not store these directly in your source code or version control, and instead should use environment variables or some other secure mechanism for storing and consuming your API keys (ex. AWS KMS).

After registering your application you will be sent an email with your client ID, or
you can get your client ID and secret right from the API console by clicking on your
application.

## Cisco Support API End-point Best Practices

Okay so at this point you have registered your application, have your client ID and
secret, and are now exploring the available API end-points to see what data you can
report on. This section won't cover the details about each API end-point (examples
will be provided in part 2), but instead will highlight a few things to keep in mind
when interacting with the API's.

Most of the API's will support returning data in JSON format, but a few also provide
XML responses. I personally prefer JSON as Python has a few packages that will easily
convert JSON into a dictionary, and JavaScript can easily convert it into an object.

!!! Note
    Play nice with Cisco's API's by rate limiting and reducing unecessary queries.

Because you are rate limited on the number of calls per second you can make, I often
include a sleep timer of 0.5s between API calls. If you let your application run wide open
you will start receiving error responses and timeouts. Play nice with Cisco's API's -
rate limit directly within your applications so you don't abuse this great service.

On the same front around rate limiting, you are limited to the number of requests you
can place per day. Most API end-points allow you to include multiple items in each
request. As an example the EoX by Product ID's (PID's) API allows you to include up to 20
PID's per request. Remember, each router can have multiple pieces of hardware installed
in it (check with a `show inventory`). A chassis PID of ISR4451/K9, a module PID of
NIM-4MFT-T1/E1, another module of PID ISR4451-X-4x1GE, and possibly more. Instead of sending
three API calls (one for each PID), you can group these together in a comma seperated
string so that you only have a single API call. Additionally, I usually deduplicate
things like the hardware PID's discovered across the entire environment I am reporting on.
If you have a dozen Cisco ISR4451/K9's in your environment, you are using you your API
call quota and Cisco's resources by querying for the same PID multiple times. Part 2
will show you an example on how to do this deduplication.

## Cisco PSIRT openVuln API

While not a Support API, Cisco does offer access to their [PSIRT openVuln API](https://developer.cisco.com/psirt/). I find this
worth mentioning because this can be a valuable tool for you to include in automations
you may be creating. If you are already reporting on bugs associated with current
software images that are in-use in an environment, including security advisory reviews
as part of your software analysis can siginificantly help drive value for your customers.

I won't be expanding on this API in this post, but may create a post in the future.

## Next Steps

I hope that this post has been informative for you. I have found Cisco's Support API's
to be helpful in driving value for my customers and I'm exciting to create a more
technical post with some Python examples. Part 2 of this series should be live in
a few days.

I am a strong believer in learning from others experiences. If you have been using Cisco's
API's, I would really like to hear how you have used them and what value the provided you. Feel
free to discuss on the social media links above!
