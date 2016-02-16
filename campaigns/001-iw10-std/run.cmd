
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

# start netperf as receiver at TCP port
# 8000 and background process. This applet
# probably copy a local python helper program
# to node beta.
# xxx- prefixed applets are not implemented yet
exec xxx-netperf-sink beta mode:background port:8000

# limit rate at forwarding radio to 10000 byte/sec
exec xxx-netem koppa rate:10000

# set IW at sender to 20
exec xxx-conf-iw alpha 20
# send 10000 byte from to beta (at node alpha)
# do not background, wait in foreground, process
# will block here until all bytes are transmitted
exec xxx-netpert-sender alpha beta 10000

# ok, if the previous process returns the data is transmitted


# now read the data at the sink. This command will
# simple return the data writen with the previous backgrounded
# "exec xxx-netperf-sink beta 8000" call. The data file
# is copied here, the file at beta is removed (cleaned)
exec xxx-netperf-sink beta stop-backgrouding
exec xxx-netperf-sink beta fetch-data


