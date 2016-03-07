
# check if all required nodes are
# up, if at least one fails test will stop
exec 001-alive alpha
exec 001-alive beta
exec 001-alive koppa

# save syscall, no-op when already done
exec 003-save-sysctls alpha
exec 003-save-sysctls beta
exec 003-save-sysctls koppa

# restore sysctls to initial default
exec 003-restore-sysctls alpha
exec 003-restore-sysctls beta
exec 003-restore-sysctls koppa


# set some specific sysctl values for sender and receiver
exec xxx-sysctl alpha set net.ipv4.tcp_no_metrics_save:1
exec xxx-sysctl koppa set net.ipv4.tcp_no_metrics_save:1


# disable offloading capabilities for sender and receiver
exec xxx-ethtool alpha "-K tso off gso off gro off sg off"
exec xxx-ethtool beta "-K tso off gso off gro off sg off"

# start netperf as receiver at TCP port
# 8000 and background process. This applet
# probably copy a local python helper program
# to node beta.
# xxx- prefixed applets are not implemented yet
exec xxx-netperf beta [sink] mode:background port:8000

# limit rate at forwarding radio to 10000 byte/sec
exec xxx-netem koppa rate:10000

# set IW at sender to 20
exec xxx-conf-iw alpha 20
# send 10000 byte from to beta (at node alpha)
# do not background, wait in foreground, process
# will block here until all bytes are transmitted
exec xxx-netpert-sender alpha beta 10000

# ok, if the previous process returns the data is transmitted

#tcpdump
exec xxx-capture-pcap beta background ofile="stream1.pcap" filter="port 8000"
exec xxx-capture-pcap beta background ofile="stream2.pcap" filter="port 8001"

# now read the data at the sink. This command will
# simple return the data writen with the previous backgrounded
# "exec xxx-netperf-sink beta 8000" call. The data file
# is copied here, the file at beta is removed (cleaned)
exec xxx-netperf-sink beta stop-backgrouding
exec xxx-netperf-sink beta fetch-data


exec xxx-capture-pcap beta fetch ofile="stream1.pcap"


