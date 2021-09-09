---
title: "Best Practices for Safe Ansible Playbook Execution"
tags:
  - Automation
  - Ansible
---

Ansible can be a very powerful automation tool, allowing you to interact with hundreds or thousands of network devices at once. The automation is defined through a combination of inventory files, variable files, and playbooks (with optional task files and roles). The combination of these features makes a very powerful automation tool, but with that comes a high-level of risk. In this guide I highlight a few best practices to follow when executing Ansible playbooks. By following these best practices you will have increased confidence that you are implementing the correct tasks against he correct set of devices, and avoid any surprises!

The ansible-playbook best practices covered in this post are:

1. Manually specifying your inventory file
2. Using the list-hosts flag to confirm the hosts are as you expect
3. Using the list-tasks flag to confirm the tasks that will be implemented

## Example Ansible Inventory and Playbook

In this post I will be using the following Ansible file structure:

```bash
byaklin@ansiblevm:~/ansible-example$ tree
.
├── ansible.cfg
├── group_vars
│   └── ios.yml
├── inventory
│   ├── hosts.yml
│   └── ios_routers.yml
└── test-pb.yml

2 directories, 5 files
```

The inventory file that we will be using is ios_routers.yml:

```yaml
---
ios:
  hosts:
    RouterA:
      ansible_host: 192.168.10.150
      syslog_servers:
        - 192.168.1.1
        - 192.168.1.2
    RouterB:
      ansible_host: 192.168.10.151
  children:
    calgary:
      hosts:
        RouterA:
    ottawa:
      hosts:
        RouterB:
```

Finally, the example playbook that I have is as shown below. The specific details about what each task does isn't important, whats important is that we have multiple tasks, some of which are related. This will become more apparent in my explanation of the list-tasks flag later on.

{% raw %}

```yaml
---
- hosts: ios
  gather_facts: False

  tasks:
    - name: Configure banner
      tags:
        - banner
      cisco.ios.ios_banner:
        banner: login
        text: "{{ banners.login }}"
        state: present

    - name: Remove MOTD banner
      tags:
        - banner
      cisco.ios.ios_banner:
        banner: motd
        text: "{{ banners.motd }}"
        state: present

    - name: Remove EXEC banner
      tags:
        - banner
      cisco.ios.ios_banner:
        banner: exec
        state: absent

    - name: Remove incoming banner
      tags:
        - banner
      cisco.ios.ios_banner:
        banner: incoming
        state: absent

    - name: Confure logging hosts
      tags:
        - logging
      ios_logging:
        dest: host
        name: "{{ item }}"
        state: present
      loop: "{{ syslog_servers }}"

    - name: Adjust local logging buffer
      tags:
        - logging
      ios_logging:
        dest: buffered
        size: 5000
        level: informational
        state: present

    - name: Configure SNMP
      tags:
        - snmp
      ios_config:
        lines:
          - snmp-server location {{ snmp.location }}
          - snmp-server contact {{ snmp.contact }}
          - snmp-server community {{ snmp.community }} ro SNMP_ACL
      no_log: True

    - name: Configure SNMP ACL
      tags:
        - snmp
      ios_config:
        lines:
          - permit {{ item }}
        parents:
          - ip access-list standard SNMP_ACL
      loop: "{{ snmp.servers }}"

    - name: Configure Local Accounts
      tags:
        - users
      ios_config:
        lines:
          - username {{ item.username }} secret {{ item.password }}
      loop: "{{ users }}"
      no_log: True

    - name: Save configuration
      tags:
        - save
      ios_config:
        save_when: modified
```

{% endraw %}

## Best Practice # 1 - Manually specifying inventory file

There are multiple ways for the ansible-playbook command to find an inventory file to execute against. This can be through the use of the ANSIBLE_INVENTORY variable, the default location of inventory/hosts.yml, by using the -i flag on the ansible-playbook command, dynamic inventory scripts, etc. With many different methods of defining your inventory, I find the safest method is to manually and explicitly identify it when executing a playbook. This ensures that if you created an inventory file for a specific change you are implementing, there is no chance of ansible-playbook picking up a different inventory file through one of the other methods. This will help you avoid uninentional changes being executed against devices you have not intended for.

In my example folder structure there are two inventory files, but the one that I want to execute my playbook against is ios_routers.yml. To specify this I use the -i flag with the ansible-playbook command:

```bash
byaklin@ansiblevm:~/ansible-example$ ls inventory/
hosts.yml  ios_routers.yml
byaklin@ansiblevm:~/ansible-example$ ansible-playbook test-pb.yml -i inventory/ios_routers.yml
```

## Best Practice # 2 - Using the ansible-playbook list-hosts flag

In addition to manually specifying the inventory file you want to execute your playbook against, there are often times where you may wish to only run the playbook against a subset of hosts in that inventory. Perhaps you have one master inventory file and you execute your playbooks against a particular group, or a hostname pattern. To confirm that you are running your playbook against the specific intended hosts, you can use the --list-hosts flag to confirm before execution that Ansible has found the correct hosts.

> You get extra bonus points if your organization has a well defined host naming convention for your network devices. Naming conventions are super helpful in conveying context, such as location or function, and can help in allowing you to use simple pattern matching with your Ansible playbooks.

When using the --list-hosts flag your playbook will not actually be executed. This gives you an opportunity to examine the returned hosts to confirm they are correct, before executing your playbook against them (by removing the --list-hosts flag):

```bash
byaklin@ansiblevm:~/ansible-example$ ansible-playbook test-pb.yml --list-hosts

playbook: test-pb.yml

  play #1 (ios): ios	TAGS: []
    pattern: ['ios']
    hosts (1):
      RouterA
```

In the above command I forgot to specify my inventory file with the -i flag. However, by using the --list-hosts flag it allowed me to spot that I was missing RouterB in the hosts that would be included as part of Play #1. I now realize my mistake, specify the host file manually and re-run my check with the --list-hosts flag to confirm that both RouterA and RouterB are now identified:

```bash
byaklin@ansiblevm:~/ansible-example$ ansible-playbook test-pb.yml -i inventory/ios_routers.yml --list-hosts

playbook: test-pb.yml

  play #1 (ios): ios	TAGS: []
    pattern: ['ios']
    hosts (2):
      RouterB
      RouterA
```

Finally, as one last example, if I only wanted to execute a playbook against a subset of my inventory by using a pattern, I can use the --list-hosts flag to ensure that my pattern is correct. In this case I only want to execute the playbook against the RouterB host.

```bash
byaklin@ansiblevm:~/ansible-example$ ansible-playbook test-pb.yml -i inventory/ios_routers.yml --limit RouterB --list-hosts

playbook: test-pb.yml

  play #1 (ios): ios	TAGS: []
    pattern: ['ios']
    hosts (1):
      RouterB
```

## Best Practice # 3 - Using the ansible-playbook --list-tasks flag

It is possible to have dozens of tasks (or more!) included in a playbook, and these can be included through separate task files, roles, etc. Depending on the purpose of your playbook and the automation that you might want to execute you may only want to implement a subset of the tasks. The ansible-playbook --list-tasks flag allows you to see which tasks will be executed. Like the --list-hosts flag previously covered, the --list-tasks flag will not actually execute your playbook. It allows you to see what will be executed, confirm it is as expected, and then you remove the flag and implement your changes.

To start, lets run the --list-tasks flag against our test-pb.yml. You can see below that we have 10 tasks, some of which are related (see the TAGS values).

```bash
byaklin@ansiblevm:~/ansible-example$ ansible-playbook test-pb.yml --list-tasks

playbook: test-pb.yml

  play #1 (ios): ios	TAGS: []
    tasks:
      Configure banner	TAGS: [banner]
      Remove MOTD banner	TAGS: [banner]
      Remove EXEC banner	TAGS: [banner]
      Remove incoming banner	TAGS: [banner]
      Confure logging hosts	TAGS: [logging]
      Adjust local logging buffer	TAGS: [logging]
      Configure SNMP	TAGS: [snmp]
      Configure SNMP ACL	TAGS: [snmp]
      Configure Local Accounts	TAGS: [users]
      Save configuration	TAGS: [save]
```

> Providing meaningful names to your tasks is very important. It helps you and anyone else using your playbook know what each task is going to do without having to read through the playbook task by task. It also helps everyone use the --list-tasks flag effectively

As an example, perhaps your organization just updated its device banner standards and only wants to run those tasks. Although Ansible tasks and modules are intended to be idempotent (only making changes when necessary and if needed), which means you could run all tasks and only the changes that are necessary (the banner) would be executed, it could drastically extend the amount of time the playbook tasks to execute. This is because Ansible needs to validate if each task needs to be made, before actually implementing it. Instead, if you know that you only want to update the banner, you can use the -t flag to specify the **banner** tag I have associated with each of those tasks. But how do you know that you didn't make a mistake when creating or specifying that tag? By using the --list-tasks flag:

```bash
byaklin@ansiblevm:~/ansible-example$ ansible-playbook test-pb.yml -t banner,save --list-tasks

playbook: test-pb.yml

  play #1 (ios): ios	TAGS: []
    tasks:
      Configure banner	TAGS: [banner]
      Remove MOTD banner	TAGS: [banner]
      Remove EXEC banner	TAGS: [banner]
      Remove incoming banner	TAGS: [banner]
      Save configuration	TAGS: [save]
```

Now we can see that only the tasks specific to updating the banner will be executed.

> I also have a specific task for saving the configuration (using the **save** tag). This helps ensure that if changes are made that they will be saved to the startup-configuration. Not all Ansible Cisco modules will do this by default (or even have the option), so instead of writing the **save_when** option on each of my tasks, I include it at the end of my playbook.

## Tying it all together

It turns out that you can use both the --list-hosts and --list-tasks flags at the same time. This allows you to validate that both the inventory and the expected tasks are correct, before you implement. The below output shows you both the hosts that were identified (in my case RouterB) and the specific tasks (banner updates, and saving the configuration):

```bash
byaklin@ansiblevm:~/ansible-example$ ansible-playbook test-pb.yml -i inventory/ios_routers.yml --limit RouterB -t banner,save --list-tasks --list-hosts

playbook: test-pb.yml

  play #1 (ios): ios	TAGS: []
    pattern: ['ios']
    hosts (1):
      RouterB
    tasks:
      Configure banner	TAGS: [banner]
      Remove MOTD banner	TAGS: [banner]
      Remove EXEC banner	TAGS: [banner]
      Remove incoming banner	TAGS: [banner]
      Save configuration	TAGS: [save]
```

Whenever I go to implement an automation using Ansible, before executing the playbook I use these options to validate that everything is as I expect it to be. I also log this information to a file and save it as part of my pre-change information gathering attached to a change record. This is to help cover myself should any unrelated issues pop-up in the network infrastructure. It's a bit of a CYA, and by showing your customers and management that you are using best practices for first verifying your playbooks (in addition to all the testing you did you with your playbook in a lab environment!), you will gain the confidence and trust from your stakeholders. This helps further promote using automation as part of your job, if you can demonstrate it being done in a safe way.
