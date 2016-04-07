
import time


def main(x):

    # print('message')
    print('Starting campaign 001-netperf-data-exchange')

    # check if all required nodes are up, if at least one fails test will stop
    x.exec('001-alive alpha')
    x.exec('001-alive beta')
    x.exec('001-alive koppa')

    # clean tmp data as well
    # /tmp/net-applet-shuffler/*
    x.exec('007-kill alpha')
    x.exec('007-kill beta')
    # only qdisc logs should be on koppa
    x.exec('007-kill koppa')

    # make sure the indirect configuration is active
    x.exec('009-network setup:indirect alpha beta')

    # save syscall, no-op when already done
    x.exec('002-save-sysctls alpha')
    x.exec('002-save-sysctls beta')
    x.exec('002-save-sysctls koppa')

    # restore sysctls to initial default
    x.exec('003-restore-sysctls alpha')
    x.exec('003-restore-sysctls beta')
    x.exec('003-restore-sysctls koppa')

    # tcpdump
    # start tcpdump on host
    # notes:
    # - [id] should be a self specified unique id string
    # - mode:start -> the local-file-name is ignored
    # usage: host id:[string] mode:[start|stop] local-file-name:"path_and_filename" filter:"tcpdump filter string"
    x.exec('006-tcpdump beta id:0001 mode:start local-file-name:"ignored" filter:"tcp and dst port 30000"')

    # netem
    # add delay to left and right outgoing interfaces for the upcoming test
    x.exec('104-netem-cmd koppa control:part change:add to-network:red command:"delay 10ms"')
    x.exec('104-netem-cmd koppa control:part change:add to-network:blue command:"delay 10ms"')

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
    x.exec('005-netperf alpha sink:beta id:0001 source_port:20000 sink_port:30000 flow_length:6 flow_offset:1 netserver:29999')
    x.exec('005-netperf beta sink:alpha id:0002 source_port:20001 sink_port:30001 flow_length:6 flow_offset:3 netserver:29998')

    # sleep seconds
    time.sleep(2)

    # blocker
    # waits for all processes to complete
    # notes:
    # - interval_time is the interval in seconds that for the completion of the processes is checked
    # - every host:id tuple actively participating in the test should be specified here
    # - one host can have several running ids, but one (unique) id can have only one host
    # usage: interval_time:[seconds] [name_1]:[id_1] [name_1]:[id_2] [name_2]:[id_3] ...
    x.exec('008-wait-for-completion interval_time:5 alpha:0001 beta:0002')

    # netem
    # cleanup, remove the added delays
    x.exec('104-netem-cmd koppa control:part change:del to-network:red command:"delay 10ms"')
    x.exec('104-netem-cmd koppa control:part change:del to-network:blue command:"delay 10ms"')

    # tcpdump
    # stop tcpdump on host, which also collects the dumpfile
    # notes:
    # - mode:stop -> the filter is ignored
    # - id and host MUST match the id of the started tcpdump
    # usage: host id:[string] mode:[start|stop] local-file-name:"path_and_filename" filter:"tcpdump filter string"
    x.exec('006-tcpdump beta id:0001 mode:stop local-file-name:"../../dumps/001_netperf_alpha_to_beta.pcap" filter:"ignored"')
