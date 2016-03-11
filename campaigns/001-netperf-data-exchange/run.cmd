
# check if all required nodes are
# up, if at least one fails test will stop
exec 001-alive alpha
exec 001-alive beta
exec 001-alive koppa

# clean tmp data as well
# /tmp/net-applet-shuffler/*
exec 002-kill beta netperf-server tcpdump netperf
exec 002-kill beta netperf-server tcpdump netperf
exec 002-kill beta netperf-server tcpdump netperf

# save syscall, no-op when already done
exec 003-save-sysctls alpha
exec 003-save-sysctls beta
exec 003-save-sysctls koppa


# restore sysctls to initial default
exec 003-restore-sysctls alpha
exec 003-restore-sysctls beta
exec 003-restore-sysctls koppa


#tcpdump
exec xxx-capture-pcap beta mode:background ofile="stream1.pcap" filter="port
8000"
exec xxx-capture-pcap beta mode:background ofile="stream2.pcap" filter="port
8001"

exec xxx-capture-pcap beta mode:background id=1 filter=port 80
exec xxx-capture-pcap beta mode:background id=2 filter=port 81
[...]
exec xxx-capture-pcap beta stop id=2



exec xxx-capture-pcap beta fetch ofile="stream2.pcap"


# xxx- prefixed applets are not implemented yet
#
# start netperf server on destination:netserver_port, connect with source, send
# [length] (-#bytes) tcp traffic from source:port to destination:port
# Usage
# xxx-netperf source dest mode:[options] sport:[port] dport:[port]
# length:[seconds|bytes] netserver:[port]
exec 005-netperf alpha beta mode:idontcareyet sport:18000 dport:18001
length:-1000000 netserver:16666


# ok, if the previous process returns the data is transmitted


# now read the data at the sink. This command will
# simple return the data writen with the previous backgrounded
# "exec xxx-netperf-sink beta 8000" call. The data file
# is copied here, the file at beta is removed (cleaned)
exec xxx-netperf-sink beta stop-backgrouding
exec xxx-netperf-sink beta fetch-data


exec xxx-capture-pcap beta fetch ofile="stream1.pcap"


