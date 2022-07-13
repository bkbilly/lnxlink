---
name: Bug report
about: Create a report to help identify the problem
title: ''
labels: ''
assignees: ''

---

**Describe the problem**
<!--  READ THIS FIRST:
  - Make sure you are running the latest version of LNXLink before reporting an issue: 
    bash <(curl -s "https://raw.githubusercontent.com/bkbilly/lnxlink/master/install.sh")
  - Provide as many details as possible. Paste logs, configuration samples and code into the backticks.
-->


**OS Version**
<!--  Provide the OS version with this command 
    lsb_release -a
-->

**LNXLink version** 
<!--  Provide the hash from the command bellow 
    git -C /opt/lnxlink/ rev-parse HEAD
-->

**Logs**
<!--  Provide the log output from the following command 
    journalctl --user -u lnxlink -n 100 --no-pager
-->
```txt

```

**Configuration**
<!--  Provide the settings, remove any sensitive info like usernames, passwords that might exist  
    cat /opt/lnxlink/config.yaml
-->
```yaml

```
