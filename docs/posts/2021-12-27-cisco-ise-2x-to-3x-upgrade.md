---
date:
  created: 2021-12-27
categories:
  - NAC
tags:
  - Cisco
  - Security
---

# Cisco ISE 2.4 to 3.0 Upgrade Procedure

If you have ever read through [Cisco ISE 3.0 Upgrade Guide](https://www.cisco.com/c/en/us/td/docs/security/ise/3-0/upgrade_guide/HTML/b_upgrade_method_3_0.html#id_121933) you know that it involves a lot of decision points and having to reference many other Cisco reference documents just to build a complete implementation plan for upgrading Cisco ISE from 2.x to 3.x. It is a complicated process if you have never been through it before, and often times you're left with more questions than answers when researching how to proceed. This usually involves engaging Cisco TAC to help clarify points that aren't necessarily obvious in their documentation. Having gone through this upgrade path this past year, I thought that documenting the procedures that I followed may help others gain success in their own upgrades. Understand that all implementations are different, so use this as another piece of information as you research how to perform this upgrade.

<!-- more -->

## Example Cisco ISE Environment

This guide is built based on the following Cisco ISE environment:

- All Cisco ISE nodes are virtual machines running on VMWare ESXi
- Nodes are deployed as follows
  - Two Admin (primary/secondary)
  - Two Monitor (primary/secondary)
  - Four PSN's
- None of the PSN's are behind load balancers
- PSN's are only being used for TACACS/RADIUS authentication, not for any discovery or dot1x authentication
- AD is used as an external identify source

!!! note
    Cisco's documentation briefly glosses over placing your PSN's behind a load balancer. I have seen this done in larger organizations, but not in smaller ones. There is definitely a benefit to using a load balancer, as it allows you to take a PSN out of rotation so that you can upgrade it and change its IP address (which will save you a few steps in this guide). You avoid causing an outage for clients using the PSN's as they are querying againt a load balancer VIP and you should only be upgrading one PSN in the load balancer pool at a time.

## Cisco ISE Upgrade Methods

Cisco provides three different methods that you can follow for upgrading Cisco ISE:

1. Backup and Restore method, which Cisco recommends but is the the most difficult to implement
2. Upgrade using the GUI, which takes more time but is the 'easiest' method to follow
3. Upgrade using the CLI, which is just slightly more difficult than using the GUI

Not all deployments are able to use each of these methods. In this particular example, the GUI and CLI options are not possible because of how the Cisco ISE 2.4 VM's were deployed. Version 3.0 [requires signinficantly more disk space](https://www.cisco.com/c/en/us/td/docs/security/ise/3-0/install_guide/b_ise_InstallationGuide30/b_ise_InstallationGuide30_chapter_2.html#ID-1417-000000d9) than version 2.4. A disk size of 300GB to 600GB are required, as a minimum, on each node regardless of its persona, compared to what many 2.4 deployments required (200GB). Cisco also advises that if you increase the disk size of your VM, you must perform a fresh installation of Cisco ISE to detect the increased capacity. There is no supported method of increasing the disk size.

The other challenge of building new PSN VM's is that without a load balancer, all of your routers, switches, and wireless controllers are referencing TACACS/RADIUS server IP addresses that exist directly on the PSN's. Cisco's documentation walks through creating new VM's with new IP addresses, which means that you will need to reconfigure all network infrastructure to point to a new TACACS/RADIUS server IP address. This can involve a significant amount of time if you're not using automation to implement this task. You do have the ability to change the IP address of the new 3.0 PSN after it has been created and the old 2.4 PSN has been shutdown, but this involves additional steps as well (e.g. having to de-register and re-register the PSN from the admin node, adjusting DNS entries). Instead, this guide walks through keeping both 2.4 and 3.0 VM's with the same IP addresses, but shutting down the 2.4 VM before building the new 3.0 VM. There is a brief moment in time where impact can be seen by the network device must wait for keepalives to fail to a PSN thats being migrated, before it starts to query a secondary PSN that isn't currently being migrated.

!!! note
    Another important aspect of upgrading from ISE 2.4 to 3.0 is that licensing changes to requiring smart licensing. If you don't yet have smart licensing, but need to perform an upgrade, you can enable the grace period license which should provide 90 days for you to continue using all necessary features until you migrade to smart licensing. The steps to adjust licensing are not covered in this guide.

## Implementation and Verification Plan

### Overview

The steps documented below outline how to migrate Cisco ISE 2.4 VM's to 3.0 VM's using the [Backup and Restore method](https://www.cisco.com/c/en/us/td/docs/security/ise/3-0/upgrade_guide/HTML/b_upgrade_method_3_0.html#id_121933). Depending on the size of your infrastructure, you may choose to migrate the PSN's over multiple change windows. This will depend on how frequenty you make changes in your environment, as you will end up having a 'split' cluster where one admin and monitor node remain on version 2.4 while another admin and monitor node are on version 3.0. Throughout multiple change windows, you can disable a version 2.4 PSN and build the 3.0 PSN. If you are frequently making policy changes, you either need to make them in both the 2.4 and 3.0 admin nodes, or migrate all PSN's during the same change window.

!!! note
    The steps to perform on VMWare ESXi are not covered in this guide. Refer to Cisco's documentation for VM requirements, and VMWare's documentation for implementation steps that might be necessary to create the VM.

### Step 0 - Pre-Change Readiness

To prepare for your migration you will want to ensure the status of multiple elements and perform backups of critical configuration and certificates. This can be accomplished as follows:

1. Login to your 2.4 Primary Admin Node (PAN).
2. Confirm all certificates are valid and not expired by browsing to **Administration > System > Certificates** and check the status of all **Trusted Certificates**.
3. For each external identity source, ensure that connectivity from each PSN to each source is OK. As an example, for AD browse to **Administration > Identity Management > External Identity Sources > Active Directory…** and for each join point check the reachability status for each PSN.
   > Identify the AD credentials which are necessary for each AD join-point. These are not restored when using the backup and restore method. Each join-point will need to be recreated later on in this guide.
4. Export any System Certificates that are used by your deployment by browsing to **Administration > System > Certificates** and clicking on **System Certificates**.
5. Export any non-default Trusted Certificates that are used by your deploymet by browsing to **Administration > System > Certificates** and clicking on **Trusted Certificates**. Many of the certificates here are CA signed certificates that will exist in ISE version 3.0 and are not necessary to manually export and re-import. Only the certificates that you have imported for your organization.
   > Certificates are not automatically restored in the backup and restore method, therefore it is critical to create a backup of these in case issues are experienced during the upgrade.
6. Document PAN auto-failover settings by browsing to **Administration > System > Deployment > PAN Failover** and documenting the status and value for all settings.
7. Perform a manual Configuration Data Backup of the Cisco ISE settings. If you require logs to be backed up and referencable in the new ISE 3.0 implementation, perform an Operational Backup (this will be significantly larger and require more time). Browse to **Administration > System > Backup & Restore**, select **Configuration Data Backup** and click on **Backup Now**. Provide the necessary details and utilize an existing backup repository.
8. SSH to each Cisco ISE node and log the output of the following commands to file. These will later be used to reconfigure the new Cisco ISE 3.0 VM's, as well as to capture the status of each VM prior to the upgrade to identify any anomalies if they happen (e.g. high CPU, application services not running, etc)
   - show clock
   - show version
   - show ntp
   - show uptime
   - show cpu usage
   - show repository
   - show application
   - show application status ise
   - show running-config
9. Ensure that a DNS entry exists for each Cisco ISE node, as this will be used as part of the re-registration process when joining a PSN to the version 3.0 ISE admin node.

### Step 1 - Create Cisco ISE 3.0 Primary Admin Node

During this step we will be disabling the version 2.4 secondary admin node (SAN) and re-creating it as the version 3.0 primary admin node (PAN).

1. Login to your 2.4 Primary Admin Node (PAN).
2. Disable PAN auto-failover by browsing to **Administration > System > Deployment > PAN Failover** and unchecking the **Enable PAN Auto Failover** option, then click save.
3. Disjoin the SAN from each AD join-point. Browse to **Administration > Identity Management > External Identity Sources**, click the **Active Directory** folder and navigate to each join-point and perform the following steps:
   1. Find the SAN and select the checkbox next to it
   2. Click the **Leave** button to Disjoin the SAN
4. De-register the SAN from the version 2.4 cluster. Browse to **Administration > System > Deployment** and check the box next to the SAN. Click the **Deregister** button and then **OK** to de-register the SAN from the cluster.
5. Shutdown the version 2.4 SAN VM in VMWare.
6. Create the ISE version 3.0 VM which will be configured with the properties of the version 2.4's SAN (except it will be the PAN of the version 3.0 cluster)
7. Once the VM is built in the hypervisor, use the serial console to connect and issue the **setup** command. This will prompt you for various parameters such as hostname, IP address, DNS and NTP servers, local admin credentials to use, etc. You can find this information from the output of the **show running-config** that was captured during step 0 of this guide.
8. After entering the initial setup parameters, the node will reload. Log back in to the CLI using the serial console and configure any remaining features by comparing the output of the **show running-config** from before the change with what is currently in the configuration. An example of what may need to be configured would be features like SNMP (enabling it, community strings, trap destinations, etc.) and any other local accounts.
9. Confirm that the node is running the correct version and patches with the **show version** command and that the ISE process is running with the **show application status ise**.
10. Browse to the IP address or FQDN of the version 3.0 PAN that has just been created and login. The web GUI's admin credentials are those that were set using the **setup** command on the CLI
    > Both the web and CLI admin credentials may start off as the _same_ credential, but Cisco ISE treats them as two completely separate accounts.
11. Set the role of the version 3.0 PAN as an admin node by browsing to **Administration > System > Deployment** and clicking on **Deployment**. Select the node from the list and enable the **Administration** role on the **General Settings** tab.
12. Browse to **Administration > System > Maintenance > Repository** and create a repository so that the backup can be imported.
13. Import this nodes system certificate by browsing to **Administration > System > Certificates** and click on **System Certificates**. Click on **Import** and fill in the details of the version 3.0 PAN and select the certificate file for this node that was exported during step 0.
14. Import all trusted certificates by browsing to **Administration > System > Certificates** and click on **Trusted Certificates**. Import each Trusted Certificate that were exported during step 0, and compare the configuration with that of the existing version 2.4 PAN that should still be accessible.
15. Create the Active Directory join-points by browsing to **Administration > Identity Management > External Identity Sources** and clicking on **Active Directory**. Once again, you can look at both the version 2.4 PAN and the new version 3.0 PAN at the same time to ensure that each join-point is created the same.
16. Join the version 3.0 PAN to each AD join-point. Under each join-points **Connection** tab click the **Join** button, select the new node from the list, provide the AD credentials gathered as part of step 0, and click submit. Confirm that the status of the node for each join-point is **Operational**.
17. Restore the ISE backup by SSH'ing to the version 3.0 PAN and logging in. Run the command **restore FILE_NAME repository REPO_NAME encryption-key plain ENC_KEY** using the repository name that was created earlier, along with the filename that was given to the backup during step 0.
18. You can monitor the backup restoration using the **show restore status** command. Once the restore has been completed, the node will reload. SSH back into this node and issue the **show application status ise** command to ensure the ISE process is running.
19. Log back into the version 3.0 PAN web GUI. Make the version 3.0 PAN the primary admin node by browsing to **Administration > System > Deployment** and click the name of the node. Under the **General Settings** click the button that says **Make Primary**.

### Step 2 - Create Cisco ISE 3.0 Primary Monitor Node

During this step we will be disabling the version 2.4 secondary monitor node (SMN) and re-creating it as the version 3.0 primary monitor node (PMN). Many of these steps are the same as in step 1 when creating the ISE 3.0 PAN, so the steps are shortened for brevity.

1. Login to your 2.4 PAN's web GUI.
2. Disjoin the SMN from each AD join-point in the version 2.4 PAN.
3. De-register the SMN in the version 2.4 PAN.
4. Shutdown the version 2.4 SMN VM (don't delete), create the new version 3.0 SMN VM and configure over the serial console using the **setup** command, referencing the **show running-config** that was captured during step 0 of this guide. The node will reload after finishing the setup, log back in and configure any remaining elements (SNMP, local accounts, etc.) by comparing the **show running-config** that was gathered in step 0 with the current output of the configuration on the version 3.0 node.
5. Validate that the node is running the proper version of software with **show version** and that the ISE process is running with **show application status ise**.
6. Login to your 3.0 PAN's web GUI.
7. Register the verison 3.0 PMN VM as the primary monitoring node by registering the node in the version 3.0 PAN.
8. Set the role of the version 3.0 PMN as a monitor node by browsing to **Administration > System > Deployment** and clicking on **Deployment**. Select the node from the list and enable the **Monitor** role on the **General Settings** tab, setting it to primary if prompted.
9. Import this nodes system certificate by browsing to **Administration > System > Certificates** and click on **System Certificates**. Click on **Import** and fill in the details of the version 3.0 PMN and select the certificate file for this node that was exported during step 0.
10. Join the node to each AD join-point and ensure that its status is **Operational**.

### Step 3 - Create Cisco ISE 3.0 Node Groups

If you use node groups in your ISE deployment, follow the steps listed below.

!!! note
    Node groups are not re-created when using the backup and restore method with Cisco ISE. They must be manually recreated.

1. Login to your 3.0 PAN's web GUI.
2. Browse to **Administration > Deployment** and under the **Deployment** column click the gear icon and **Create Node Group**.
3. Create the node groups by also logging into your version 2.4 PAN and comparing the configuration with your new version 3.0 PAN.

### Step 4 - Create Cisco ISE 3.0 Policy Service Nodes

During this step we will be disabling a version 2.4 policy service node (PSN) and re-creating it as a version 3.0 PSN. Many of these steps are the same as in step 1 when creating the ISE 3.0 PAN, so the steps are shortened for brevity. Perform each of these steps for each PSN, but only migrate one PSN at a time.

!!! note
    At this stage, you may choose to migrate PSN's across multiple change windows depending on your organizations needs. However, if you need to make any policy configuration changes in Cisco ISE you will need to perform identical changes in both the version 2.4 and 3.0 PAN's. There will also be a period in time where the admin and monitor nodes of each cluster are not redundant.

1. Login to your 2.4 PAN's web GUI.
2. Disable the Policy Service feature for this node so that it will no longer respond to TACACS/RADUS requests (allowing any network device that used this PSN to mark it as down after a period of time and reference another PSN), by browsing to **Administration > System > Deployments**, clicking on the node, navigating to the **General Settings** tab and deselecting the checkbox for **Policy Service**, then click **Save**.
3. Disjoin the PSN from each AD join-point in the version 2.4 PAN.
4. De-register the PSN in the version 2.4 PAN.
5. Shutdown the version 2.4 PSN VM (don't delete), create the new version 3.0 PSN VM and configure over the serial console using the **setup** command, referencing the **show running-config** that was captured during step 0 of this guide. The node will reload after finishing the setup, log back in and configure any remaining elements (SNMP, local accounts, etc.) by comparing the **show running-config** that was gathered in step 0 with the current output of the configuration on the version 3.0 node.
6. Validate that the node is running the proper version of software with **show version** and that the ISE process is running with **show application status ise**.
7. Login to your 3.0 PAN's web GUI.
8. Register the verison 3.0 PSN VM in the version 3.0 PAN's deployment.
9. Import this nodes system certificate by browsing to **Administration > System > Certificates** and click on **System Certificates**. Click on **Import** and fill in the details of the version 3.0 PSN and select the certificate file for this node that was exported during step 0.
10. Join the node to each AD join-point and ensure that its status is **Operational**.
11. Set the role of the version 3.0 PSN by browsing to **Administration > System > Deployment** and clicking on **Deployment**. Select the node from the list and enable the **Policy Service** role on the **General Settings** tab and compare the remaining settings to that of the node in your version 2.4 PAN's web GUI.
12. Login to various network devices that are configured with this PSN and issue **test aaa...** type commands to confirm reachability to the PSN, as well as that the PSN can authenticate a test user ID using its AD join-points. You can also monitor live requests via the version 3.0 PAN by browsing to **Operations > RADIUS > Live Logs** and **Operations > TACACS > Live Logs** to see incoming TACACS/RADIUS requests and if they are successfully authenticated/authorized.

### Step 5 - Create Cisco ISE 3.0 Secondary Monitor Node

During this step we will be disabling the version 2.4 primary monitor node (PMN) and re-creating it as the version 3.0 secondary monitor node (SMN). Follow the same steps that are used in step 2, but when setting the role of this SMN, if prompted set it to secondary.

### Step 6 - Create Cisco ISE 3.0 Secondary Admin Node

During this step we will be disabling the version 2.4 primary admin node (PAN) and re-creating it as the version 3.0 secondary admin node (SAN). Follow many of the same steps that are used in step 2, but when setting the role of this SAN, set it to Admin and if prompted mark it as secondary.

### Step 7 - Promote Cisco ISE 3.0 Admin and Monitor Nodes (Optional)

During this step we will be promoting the version 3.0 secondary admin and monitor nodes to primary, to match that of the previous version 2.4 deployment. If you do not have a requirement for specific nodes to be primary and other nodes to be secondary, you can ignore this step.

1. Login to your 3.0 SAN's web GUI.
2. Browse to **System > Deployment** and click the button **Promote to Primary**
3. Validate the health of the new admin node by browsing to **System > Deployment** and confirming that the **Node Status** is green for all nodes.
4. Confirm that all nodes have connectivity to each AD join-point.
5. Browse to **System > Deployments** and select the current PMN. In the **Monitoring** section change the role from **Primary** to **Secondary**.

### Step 8 - Re-Enable PAN Auto-Failover

During this step we will be re-enabling the PAN auto-failover feature which was disabled in step 1.

1. Login to your 3.0 Primary Admin Node (PAN).
2. Enable PAN auto-failover by browsing to **Administration > System > Deployment > PAN Failover** and checking the **Enable PAN Auto Failover** option. Set the auto-failover settings that were documented during step 0, then click save.

### Backout Plan

Should you need to backout to the version 2.4 Cisco ISE environment you should have all of the version 2.4 VM's in a shutdown state on their respective hypervisors. Although this consumes space and resources on the hypervisory, it is beneficial to keep these around for several weeks until the new version 3.0 environment is confirmed operational. However, if issues are encountered and you need to backout to version 2.4 you shutdown the version 3.0 VM's and re-enable the version 2.4 VM's in a similar order to how you migrated from 2.4 to 3.0. You will need to re-register and join to the AD join-points for each node.
