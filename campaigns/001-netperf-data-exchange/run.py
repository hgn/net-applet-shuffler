
import random
import time
import timetracker


def main(x):
    tt = timetracker.TimeTracker("001-netperf-data-exchange")
    # print('message')
    print('Starting campaign 001-netperf-data-exchange')
    print(tt.get_campaign_runtime()[0])

    # check if all required nodes are up, if at least one fails test will stop
    x.exec('001-alive alpha')
    x.exec('001-alive beta')
    x.exec('001-alive koppa')

    # clean running interfering processes
    # clean tmp data /tmp/net-applet-shuffler/*
    # clean possible qdiscs
    x.exec('007-kill alpha')
    x.exec('007-kill beta')
    # only qdisc logs should be on koppa
    x.exec('007-kill koppa')

    # make sure the dumbbell configuration is active
    # also sets up basic routing (default gateways)
    x.exec('009-network setup:dumbbell alpha beta')

    tt.add_poi("alive-kill-network_time")

    # save syscall, no-op when already done
    x.exec('002-save-sysctls alpha')
    x.exec('002-save-sysctls beta')
    x.exec('002-save-sysctls koppa')

    # restore sysctls to initial default
    x.exec('003-restore-sysctls alpha')
    x.exec('003-restore-sysctls beta')
    x.exec('003-restore-sysctls koppa')

    # netem
    # add delay to left and right outgoing interfaces for the upcoming test
    # restoration is covered by 007-kill
    # notes:
    # - careful with the delete qdisc command, it will stop the campaign with an error if there is no qdisc to be deleted
    x.exec('104-netem-cmd koppa control:partial change:add to-network:red command:"delay 10ms"')
    x.exec('104-netem-cmd koppa control:partial change:add to-network:blue command:"delay 10ms"')

    # min rto
    # usage: [host] min-rto:[time] change:[add|del]
    # restoration is covered by 009-network
    # or by using the standard 200ms
    x.exec('103-tcp-min-rto alpha min-rto:10ms')
    x.exec('103-tcp-min-rto beta min-rto:10ms')

    # tcp iw
    # usage: [host] initcwnd:[number] initrwnd:[number]
    # restoration is covered by 009-network
    x.exec('101-tcp-iw alpha initcwnd:20 initrwnd:20')
    x.exec('101-tcp-iw beta initcwnd:20 initrwnd:20')

    # tcp route metrics save
    # usage: [host] route-metrics-save:[enabled|disabled]
    # restoration is covered by 003-restore-sysctls
    x.exec('102-tcp-route-metrics alpha route-metrics-save:disabled')
    x.exec('102-tcp-route-metrics beta route-metrics-save:disabled')

    # interface offloading
    # usage: [host] command:"[command]"
    # restoration has to be covered manually (see end of run)
    x.exec('105-offloading alpha offloading:off')
    x.exec('105-offloading beta offloading:off')

    # tcpdump
    # start tcpdump on host
    # notes:
    # - [id] should be a self specified unique id string
    # - mode:start -> the local-file-name is ignored
    # - make sure the filter is valid, otherwise tcpdump won't create a file
    # usage: host id:[string] mode:[start|stop] local-file-name:"path_and_filename" filter:"tcpdump filter string"
    x.exec('006-tcpdump beta id:0001 mode:start filter:"tcp and dst port 30000"')

    tt.add_poi("setup_time")

    # netperf
    # start netperf sink, connect to it from host (source) and start a transfer
    # notes:
    # - a default netserver will run on port 12865 (if kill applet was not used)
    # - data will flow from host (source) to sink
    # - [name] is the hostname specified in the conf.json
    # - flow_length is in seconds, or if negative, in bytes
    # - flow_offset is the time in seconds after which the flow is started
    # - netserver is the control(!) port of the netserver
    # usage: host sink:[name] id:[string] source_port:[port] sink_port:[port] flow_length:[seconds|-bytes] flow_offset:[seconds] netserver:[port]
    x.exec('005-netperf alpha sink:beta id:0002 source_port:20000 sink_port:30000 flow_length:6 flow_offset:1 netserver:29999')
    x.exec('005-netperf beta sink:alpha id:0003 source_port:20001 sink_port:30001 flow_length:6 flow_offset:3 netserver:29998')

    # blocker
    # waits for all processes to complete
    # notes:
    # - interval_time is the interval in seconds that for the completion of the processes is checked
    # - every host:id tuple actively participating in the test should be specified here
    # - one host can have several running ids, but one (unique) id can have only one host
    # usage: interval_time:[seconds] [name_1]:[id_1] [name_1]:[id_2] [name_2]:[id_3] ...
    x.exec('008-wait-for-id-completion interval_time:5 alpha:0002 beta:0003')

    tt.add_poi("test_completion_time")

    # tcpdump
    # stop tcpdump on host, which also collects the dumpfile
    # notes:
    # - mode:stop -> the filter is ignored
    # - id and host MUST match the id of the started tcpdump
    # usage: host id:[string] mode:[start|stop] local-file-name:"path_and_filename" filter:"tcpdump filter string"
    x.exec('006-tcpdump beta id:0001 mode:stop local-file-name:"./campaigns/001-netperf-data-exchange/dumps/dump.pcap"')

    # netem
    # manual cleanup, remove the added delays
    # not mandatory due to being covered by 007-kill
    x.exec('104-netem-cmd koppa control:partial change:del to-network:red')
    x.exec('104-netem-cmd koppa control:partial change:del to-network:blue')

    # interface offloading
    # enable interface offloading again
    x.exec('105-offloading alpha offloading:on')
    x.exec('105-offloading beta offloading:on')

    # sleep seconds
    time.sleep(random.randrange(10))

    print(tt.update_campaign_runtime()[0])
