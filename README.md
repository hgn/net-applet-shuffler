
# Requirements #

## System Requirement ##

* Ubuntu 15.10

## Required Software ##

```
sudo apt-get install python3 foobar
sudo apt-get install netperf
```

# System Setup #

## Passwordless SSH and Sudo Access ##

Notes:
- Make sure ssh servers are running (in ubuntu 15.10 this is not the case)
- After ssh key distribution, the machine in question has to be restarted (or
a logout has to happen).

```
alpha, beta, koppa:
sudo visudo

Append to the end of file of alpha, beta and koppa (careful, this is a
possible security leak!):
[username] ALL=NOPASSWD: ALL

Use RSA key pair for remote login:
alpha:
ssh-keygen
ssh-copy-id user@beta
ssh-copy-id user@koppa

Remote log in once for key unlocking (to both servers), e.g. (perform LOGOUT
or RESTART first!):
ssh ["beta", "koppa"]@[ip] sudo apt-get update
```


## Static Route Configuration and Static ARP Entries #

Configure static routes and add static ARP entries. Static
arp entries are required to reduce measurement noise. Also, enable ip forward
on the router.
Note: These changes will be lost on a restart.

```
alpha:
[sudo] ip link set dev enp4s0 down
[sudo] ip a add 10.0.0.1/24 dev enp4s0
[sudo] ip r add default via 10.0.0.205
[sudo] ip link set dev enp4s0 up

beta:
[sudo] ip link set dev eth0 down
[sudo] ip a add 10.0.1.1/24 dev eth0
[sudo] ip r add default via 10.0.1.205
[sudo] ip link set dev eth0 down

koppa:
[sudo] ip link set dev left down
[sudo] ip link set dev right down
[sudo] ip a add 10.0.0.205/24 dev left
[sudo] ip a add 10.0.1.205/24 dev right
[sudo] ip link set dev left up
[sudo] ip link set dev right up
[sudo] echo 1 > /proc/sys/net/ipv4/ip_forward
```


## Helpful hints #

Normally, routing information is lost after a shutdown. One possible solution
is to enable ssh access via ssh on os startup, then use ssh for further
customization. An example workflow for Ubuntu 15.10 is the following:

```
- PREVENT OS FROM OVERWRITING CHANGES:
    E.g. Ubuntu has a habit to override manual changes on layer 3.
    To prevent this, go to Network Settings and open "Edit Connections...".
    Select the interface(s) in question and open "Edit". Uncheck "Automatically
    connect to this network when it is available"


[on alpha]
[network.sh]
#!/bin/bash
sudo ifconfig enp4s0 down
sleep 1
sudo ip a add 10.0.0.1/24 dev enp4s0
sleep 1
sudo ifconfig enp4s0 up
sleep 1
sudo ip r add default via 10.0.0.205
[/network.sh]
sudo /home/alpha/network.sh

[on beta]
sudo touch /etc/init.d/startup.sh
sudo vim /etc/init.d/startup.sh
[startup.sh]
#!/bin/bash
echo "Configuring Network parameters..."
sleep 10
sudo ip link set dev enp3s2 down
sudo ip link set dev enp0s25 down
sleep 1
sudo ip a add 10.0.1.1/24 dev enp0s25
sleep 1
sudo ip link set dev enp0s25 up
sleep 1
sudo ip r add default via 10.0.1.205
echo "Configuring network parameters done!"
[/startup.sh]
sudo chmod ugo+x /etc/init.d/startup.sh
sudo update-rc.d myscript defaults

[on koppa]
...
[startup.sh]
#!/bin/bash
echo "Configuring Network parameters..."
sleep 10
sudo ip link set dev enp3s2 down
sudo ip link set dev enp0s25 down
sleep 1
sudo ip a add 10.0.0.205/24 dev enp3s2
sudo ip a add 10.0.1.205/24 dev enp0s25
sleep 1
sudo ip link set dev enp3s2 up
sudo ip link set dev enp0s25 up
sudo echo 1 > /proc/sys/net/ipv4/ip_forward
echo "Configuring network parameters done!"
[/startup.sh]
...

Now every interface in question should be able to ping any.
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
