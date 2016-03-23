
# xxx- prefixed applets are not implemented yet


# check if all required nodes are up, if at least one fails test will stop
exec 001-alive alpha
exec 001-alive beta
exec 001-alive koppa


#exec 500-ip alpha set-direct-conf
#exec 500-ip beta set-direct-conf


# clean tmp data as well
# /tmp/net-applet-shuffler/*
exec 007-kill alpha
exec 007-kill beta


# save syscall, no-op when already done
exec 002-save-sysctls alpha
exec 002-save-sysctls beta
exec 002-save-sysctls koppa


# restore sysctls to initial default
exec 003-restore-sysctls alpha
exec 003-restore-sysctls beta
exec 003-restore-sysctls koppa

#exec netperf host mode:transmission id:foo [args, arg2]
#exec netperf host1 mode:transmission id:foo [args, arg2]

#exec netperf host mode:collect alpha:0001 beta:0002

# tcpdump
# start tcpdump on host
# notes:
# - [id] should be a self specified unique id string
# - mode:start -> the local-file-name is ignored
# usage: host id:[string] mode:[start|stop] local-file-name:"path_and_filename" filter:"tcpdump_filter_string"
exec 006-tcpdump beta id:0001 mode:start local-file-name:"ignored" filter:"tcp and dst port 30000"


# netperf
# start netperf sink, connect to it from host (source) and start a transfer
# notes:
# - a default netserver will run on port 12865 (if kill applet was not used)
# - data will flow from host (source) to sink
# - [name] is the hostname specified in the conf.json
# - flow_length is in seconds, or if negative, in bytes
# - flow_offset is the time in seconds after which the flow is started
# - netserver is the control(!) port of the netserver
# - IMPORTANT: due to command and distribution problems on congested networks,
#               the flow offsets should include enough time for setup
# usage: host sink:[name] id:[string] source_port:[port] sink_port:[port] flow_length:[seconds|-bytes] flow_offset:[seconds] netserver:[port]
exec 005-netperf alpha sink:beta id:0001 source_port:20000 sink_port:30000 flow_length:20 flow_offset:5 netserver:29999
exec 005-netperf beta sink:alpha id:0002 source_port:20001 sink_port:30001 flow_length:20 flow_offset:10 netserver:29998


sleep 4


# blocker
# waits for all processes to complete
# notes:
# - interval_time is the interval in seconds that for the completion of the processes is checked
# - every host:id tuple actively participating in the test should be specified here
# - one host can have several running ids, but one (unique) id can have only one host
# usage: interval_time:[seconds] [name_1]:[id_1] [name_1]:[id_2] [name_2]:[id_3] ...
exec 008-wait-for-completion interval_time:1 alpha:0001 beta:0002


# tcpdump
# stop tcpdump on host, which also collects the dumpfile
# notes:
# - mode:stop -> the filter is ignored
# - id MUST match the id of the started tcpdump
# usage: host id:[string] mode:[start|stop] local-file-name:"path_and_filename" filter:"tcpdump_filter_string"
exec 006-tcpdump beta id:0001 mode:stop local-file-name:"/tmp/dumps/001_netperf_alpha_to_beta" filter:"ignored"
