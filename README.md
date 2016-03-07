
# Requirements #

## System Requirement ##

* Ubuntu 15.10

## Required Software ##

```
sudo apt-get install python3 foobar
```

# System Setup #

## Passwordless SSH and Sudo Access ##

Note: After key distribution, the machine in question has to be restarted (or
a logout has to happen).

```
alpha, beta, koppa:
sudo visudo

Append to the end of file of alpha, beta and koppa (careful, this is a
possible security leak!):
USER ALL=NOPASSWD: ALL

Use RSA key pair for remote login:
alpha:
ssh-keygen
ssh-copy-id user@beta
ssh-copy-id user@koppa

Remote log in once for key unlocking (to both servers), e.g. (perform LOGOUT
or RESTART first!):
ssh ["beta", "koppa"]@localhost sudo sysctl -a > /dev/null
```

## Static Route Configuration and Static ARP Entries #

Configure static routes and add static ARP entries. Static
arp entries are required to reduce measurement noise. Also, enable ip forward
on the router.
Note: These changes will be lost on a restart.

```
alpha:
[sudo] ifconfig enp4s0 down
[sudo] ip a add 10.0.0.1/16 dev enp4s0
[sudo] ip r add default via 10.0.0.205
[sudo] ifconfig enp4s0 up

beta:
[sudo] ifconfig eth0 down
[sudo] ip a add 10.0.1.1/16 dev eth0
[sudo] ip r add default via 10.0.1.205
[sudo] ifconfig eth0 up

koppa:
[sudo] ifconfig left down
[sudo] ifconfig right down
[sudo] ip a add 10.0.0.205/16 dev left
[sudo] ip a add 10.0.1.205/16 dev right
[sudo] ifconfig left up
[sudo] ifconfig right up
[sudo] echo 1 > /proc/sys/net/ipv4/ip_forward

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

Set rate to 1000 byte/sec at koppa towards alpha (left interface):

```
./nas.py exec 005-netem koppa interface:left rate:1000byte
```

# ToDo #

* Ethernet Offloading on/off applet
* The configuration must be splitted into all interfaces per node (middlebox has two interfaces)
