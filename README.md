
# Requirements #

## System Requirement ##

* Ubuntu 15.10

## Required Software ##

```
sudo apt-get install python3 foobar
```

# System Setup #

## Passwordless SSH and Sudo Access #

```
echo fff > fff
```

## Static Route Configuration and Static ARP Entries #

Configure static routes and add static ARP entries. Static
arp entries are required to reduce measurement noise.

```
ip route add ...
```

# Examples #


Save sysctls at PC beta:

```
./nas.py exec 003-save-sysctls beta
```


Restore sysctls at PC beta:

```
./nas.py exec 003-save-sysctls beta
```

# ToDo #

* Ethernet Offloading on/off applet
* The configuration must be splitted into all interfaces per node (middlebox has two interfaces)
