# Welcome to Net Applet Shuffler #

The net-applet-shuffler or short nas is a network test framework for testing
and analysis. Conceptual similar to UNIX design philosophy: "do one thing, do
it well" is nas the lowest building block for network testing.

Nas will execute so called applets on a particular machine. Examples are:

* setting special sysctls on all receiver machines
* rate limiting (via netem) the bandwidth at all middle boxes
* start n netperf client and server instances and transmit m bytes each
* capture PCAP files on machine "alpha" and "beta" and download the file locally when netperf is finished

See the end of this file for more examples!

Writing own applets is simple, nas already provides some common
functionality for you. For example wrapping ssh and scp.

Executing applets one after another manually by hand is error prone and
unnecessary. Nas provides a higher level abstraction to merge combined
test-applets into so called campaigns. With campaigns you define your tests.
After the campaign is executed all required applets are shuffled to the correct
test boxes, the tests are executed and the results are downloaded to the local
machine.

What do you need? Probably you need as many as required hardware machines. If you
want to test within a typical bumbbell topology you need probably 5 machines.
Simple request/reply test can be done on one machine too.


# Requirements #

## System Requirement ##

* Ubuntu 15.10

## Required Software ##

```
sudo apt-get install python3 foobar
sudo apt-get install netperf
sudo apt-get install ssh
```

# System Setup #

## Passwordless SSH and Sudo Access ##

Notes:
- Make sure ssh servers are running (in ubuntu 15.10 by default this is not the case)
- After ssh key distribution, the machine in question has to be restarted (or
a logout has to happen).
- Every host which wishes to connect to another at some point in time has to be
on it's known hosts file (IMPORTANT, e.g. if the main controller is alpha, even
beta has to be able to ssh inti itself and alpha!)
- The rsa identity path is hard coded to /home/[USER]/.ssh/id_rsa (default path)

```
alpha, beta, koppa:
sudo visudo

Append to the end of file of alpha, beta and koppa (careful, this is a
possible security leak!):
[username] ALL = NOPASSWD: ALL

Use RSA key pair and distributed public key for remote login (make sure this
is done for every machine which needs to connect to another):
[on alpha]
ssh-keygen
[ssh-copy-id beta@10.0.1.1]
ssh-copy-id user@[ip]
```


## Static Route Configuration and Static ARP Entries #

Configure static routes and add static ARP entries. Static
arp entries are required to reduce measurement noise. Also, enable ip forward
on the router.

Notes:
- These changes will be lost on a restart
- The test networks are expected to use a /24 net-mask
- The direct network is expected to us a /16 net-mask
- If an outer host, which is uninvolved in the tests (except for controlling) is
used, make sure every host has ip forwarding enabled, so that the status of the
test interfaces of the test hosts can be checked

```
look at "Configuration"
```


# Helpful hints #


## Getting started ##

As a starter, it is advised to have a look at the 001-netperf-data-exchange campaign.
It acts as an example campaign of a possible (simple) workflow. Also, a lot of information
can be found in it concerning campaign setup, applet usage and hints.

Help on applet level is available for some applet by adding an "?" to the applet arguments.


## Configuration ##

The setup is stored in a file called conf.json in the nas directory root.
Hosts are expected have at least one test interface (where the tests will run),
and one control interface (where setup and test information is shared).
This is due to the reason, that if only one interface is used, this interface is
basically unavailable during heavy testing periods and the resulting congestion.
The existing nas framework provides a certain robustness to congestion on the control interfaces, so
only one single interface can theoretically be used for certain test. However,
this is not advised. Still, every host needs to have at least one control type
interface and one test type interface specified in the conf.json. These might specify the
same interface, if separated interfaces are not available.

Normally, routing information is lost after a shutdown. One possible solution
is to enable ssh access via ssh on os startup, then use ssh for further
customization. An example workflow for Ubuntu 15.10 is the following:

```
- PREVENT OS FROM OVERWRITING CHANGES:
    E.g. Ubuntu has a weird habit to sometimes override manual changes on layer 3.
    To prevent this, go to Network Settings and open "Edit Connections...".
    Select the interface(s) in question and open "Edit". Uncheck "Automatically
    connect to this network when it is available".


[on alpha]
sudo touch /etc/init.d/startup.sh
sudo vim /etc/init.d/startup.sh
[startup.sh]
#!/bin/bash
echo "Configuring Network parameters..."
sleep 15
sudo ip link set dev enp4s0 down
sudo ip link set dev enp5s5 down
sleep 1
sudo ip a add 10.0.0.1/24 dev enp4s0
sudo ip a add 10.1.0.1/16 dev enp5s5
sleep 1
sudo ip link set dev enp4s0 up
sudo ip link set dev enp5s5 up
sleep 1
sudo ip r add default via 10.0.0.205
sudo sysctl -w /net/ipv4/ip_forward="1"
echo "Configuring network parameters done!"
[/startup.sh]
sudo chmod ugo+x /etc/init.d/startup.sh
sudo update-rc.d startup.sh defaults


[on koppa]
...
[startup.sh]
#!/bin/bash
echo "Configuring Network parameters..."
sleep 15
sudo ip link set dev enp0s25 down
sudo ip link set dev enp3s0 down
sudo ip link set dev enp3s2 down
sleep 1
sudo ip a add 10.0.0.205/24 dev enp0s25
sudo ip a add 10.1.0.205/16 dev enp3s0
sudo ip a add 10.0.1.205/24 dev enp3s2
sleep 1
sudo ip link set dev enp0s25 up
sudo ip link set dev enp3s0 up
sudo ip link set dev enp3s2 up
sudo sysctl -w /net/ipv4/ip_forward="1"
echo "Configuring network parameters done!"
[/startup.sh]
...


[on beta]
...
[startup.sh]
#!/bin/bash
echo "Configuring Network parameters..."
sleep 15
sudo ip link set dev enp0s25 down
sudo ip link set dev enp3s2 down
sleep 1
sudo ip a add 10.0.1.1/24 dev enp0s25
sudo ip a add 10.1.1.1/16 dev enp3s22
sleep 1
sudo ip link set dev enp0s25 up
sudo ip link set dev enp3s2 up
sleep 1
sudo ip r add default via 10.0.1.205
sudo sysctl -w /net/ipv4/ip_forward="1"
echo "Configuring network parameters done!"
[/startup.sh]
...


Now every interface in question should be able to ping any.
```


# Examples #


Save sysctls at PC beta:

```
python3.5 ./nas.py exec-applet 003-save-sysctls beta
```


Restore sysctls at PC beta:

```
python3.5 ./nas.py exec-applet 003-save-sysctls beta
```

Set rate to 1000 byte/sec at koppa towards alpha (left interface):

```
python3.5 ./nas.py exec-applet 005-netem koppa interface:left rate:1000byte
```

Execute netperf data exchange campaign:

```
python3.5 ./nas.py -v exec-campaign 001-netperf-data-exchange
```
