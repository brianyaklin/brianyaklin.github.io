---
title: "The Role of Automated Health Checks"
tags:
  - Automation
  - Operations
  - AIOps
---

The increasing complexity of network infrastructure devices has drastically changed what is required to perform a thorough health check to ensure it is operating correctly and efficiently.
Take for example SD-WAN; what used to be a relatively simple health check on a router now requires deeper knowledge of the specific traffic traversing the device. In the past a few checks of system health (CPU, memory, hardware status, interface status and errors, routing changes) has now evolved to also include app-routing and application aware functions (app routes, SLA's, BFD, NetFlow, QoS, among many others). Health checks on a site router can now consume valuable time in driving the incident to resolution. Then take into account all of the devices in a network path between a source and destination, of which many of these devices now include rapidly evolving network technologies, and it becomes a painful battle to beat the clock as your business is being impacted by a critical incident.

As network engineers we're used to everyone else saying "it's the network causing the issue" and having to painstakenly investigate every component and provide evidence as to whether or not the network is contributing to the issue the users or applications are experiencing. It's not that I don't mind this approach, it certainly makes me a better engineer having prove without a doubt that the network is healthy, but we are always faced with prioritizing which checks we perform first and can sometimes overlook a symptom early on in an investigation as the attendees on a 30 person conference call are asking for minute-by-minute updates. When faced with limited time to perform a task you start to look for a more efficient way; automation.

Automation can be a powerful tool and as our understanding and acceptance of the risk versus reward factor increases we will find more ways to incorporate it in our daily lives in network operations. I believe that it can be a low risk and high reward when it comes to health checks and I often have the following goals when creating automated health checks:

- An automation should compliment, not replace, our monitoring tools
- Automate the easy and mundane health checks, so you can focus on the complex aspects
- Low risk tasks only, nothing dangerous
- Record a historical snapshot of current state

> By creating automations to help you during critical incidents you also provide significant value to even low priority incidents. While automations may seem overkill for a low priority and low impacting incident, you may catch an unrelated issue and be able to resolve it before there is noticeable impact to users and services. Because scripts can be executed and completed in less than a few minutes, performing due diligence on these simpler incidents can save your organization in the long run.

I hope to cover each of these goals throughout this post to provide some insight into the benefits of automated health checks.

## Where does AIOps come in to play?

Before diving into my approach to automated health checks I wanted to briefly bring up AIOps (artificial intelligence for IT operations). Any article on automation and health checks would probably be doing itself a diservice without mentioning AIOps. AIOps is the idea of leveraging machine learning (ML) and artificial intelligence (AI) to analyze large data sets to identify trends that may become, or already are, impacting. The ability of ML and AI to parse and correlate data from multiple different sources in realtime is why AIOps is starting to take off. It is used in a few different areas of IT such as security monitoring and application performance monitoring. To be completely honest I don't have any experience with platforms providing AIOps, but I'm excited to see how AIOps will evolve and help us in our roles as network engineers. Even without more complex network platforms being developed, existing platforms contain a large amount of information just waiting for a system to analyze it and provide insights that would be difficult for someone to do manually on a repeated basis.

## Monitoring Tools Have Their Place

Automating health checks should not replace your monitoring tools, they should compliment them. Monitoring tools will have a historical perspective that can be very valuable during an investigation, such as performance metrics on interface statistics, CPU/memory utilization, and other events. This historical information should still be used to identify a baseline for what things look like during periods of time where no issues are being experienced. Additionally, monitoring tools can't catch every issue or may miss an event depending on the telemetry used (syslog and SNMP traps can be unreliable during times of network instability). Your health check scripts can be used as a second set of eyes to backup and validate what your monitoring tools are showing you.

While many of the health checks that we perform can be done from within your monitoring tools, they don't solve the aspect of saving you a ton of time because you still need to manually load each network element within the monitoring tool and visually validate the status of each aspect of that device. There can be lots of eye candy that distract your eyes from looking at the relevant information, or you need to browse through multiple pages to get the information you need. This is still better than manually pulling all of the information from each network devices CLI or web GUI, as a monitoring tool can have contextual highlighting to indicate what might be an issue.

It is very difficult for monitoring tools to build in business context and to understand the intention of each network element. You as the engineer understand that context and can build that into your automated health checks.

## Automate the Easy and Mundane

Building out complex logic within a health check script will most likely require a high-level of on-going management and changes to that script as you discover edge cases. Instead, I focus on the top 15 to 20 checks I would perform on a specific device type that are easy to analyze. The following are some examples but note that each of these may have several checks to accomplish the goal of validating the component is operating in a healthy state:

- Critical interface status, speed, duplex and errors
- CPU and memory utilization
- Hardware health
- Routing protocol neighbor status (are the neighbors up, and receiving routes/prefixes, have they recently re-converged)
- Specific route status (ex. is my default-route using the correct next-hop?)
- High-Availability (HA) status (ex. firewall HA, FHRP's, routing-engines, etc)
- Recording and displaying the 15 latest high-priority logging messages (ex. syslog severity levels 0 through 2)
- Checks for any known historical and recurring issues (ex. I'm currently facing a bug on Cisco ENCS devices where a log file fills up and causes some instability)

> By having a standardized and templated network design that is applied across your organization, it will be far easier to create automated health checks (and even manual health checks!). Introducing one-off configuratons will require your health check scripts to be far more complex and decreases the accuracy of the returned results.

Once you have automated these more common health check tasks, you can run these to provide you with feedback within a minutes and know if the device is experiencing any common issues. You can also check more devices at a faster rate than you would ever be able to do manually. And once you know the general status of the network devices in the path between a source and destination you can focus on more complex areas of investigation on those devices if your scripts did not find anything relevant to the incident.

## Low Risk Tasks Only, Nothing Dangerous

During a high-impact incident the last thing you want to do is introduce further impact. The health check scripts that I have used don't perform any configuration changes or enable any debugs/traces. These are the more complex tasks that you should be performing manually or letting the network infrastructure directly implement (ex. an SLA failure causing app-aware routing to adjust on a Viptela vEdge device to a more favorable transport).

## Historical Snapshot of Current State

Having worked in network operations for the majority of my career I'm quite familiar with having to perform a post-incident review when not having been involved in the original investigation. Often times there can be a lot of debate around whether the appropriate actions were taken and if they were implemented in a timely fashion. Without sufficient data backing up our investigation it can be difficult to identify exactly what the state was during and after an incident. By automating health checks you can log a significant amount of information (ex. CLI output) to file and then record that information in an incident ticket. With this data gathering is only taking seconds to obtain, there is no reason not to gather a significant amount of information regardless of if you think it relevant at the time you are investigating.

Because this information only takes a minute or two to obtain you can gather additional snapshots throughout an incident as the symptoms change. These snapshots are helpful in understanding what the state of your network was at specific times.

Additionally, if during an incident a temporary workaround was put in place so that a vendors TAC team can be engaged to assist with root cause investigation, the information you obtained before implementing the temporary fix can be extremely useful by ensuring the vendor has as much information available to them as possible. This places you in a better position for identifying a permanent fix.

## Conclusion

Automated health checks are just one of the ways that you can implement automation within your environment. They are a low-risk high-reward type of automation that can save you significant time, reduce mean-time-to-repair (MTTR) and increase confidence and value within your organization. These types of health checks should focus on the easy tasks while you the engineer focus on the more complex tasks of an investigation. In upcoming posts I would like to cover a few methods that can be used to perform these health checks, common Python packages used, and a few examples. Stay tuned!
