
import timetracker


def main(x):
    tt = timetracker.TimeTracker("003-del-acks")
    print(tt.get_campaign_runtime()[0])
    # check if all required nodes are up, if at least one fails test will stop
    x.exec('001-alive alpha')
    x.exec('001-alive beta')
    x.exec('001-alive koppa')

    x.exec('002-save-sysctls alpha')
    x.exec('002-save-sysctls beta')
    x.exec('002-save-sysctls koppa')
    x.exec('003-restore-sysctls alpha')
    x.exec('003-restore-sysctls beta')
    x.exec('003-restore-sysctls koppa')

    x.exec('201-tcp-route-metrics alpha route-metrics-save:disabled')
    x.exec('201-tcp-route-metrics beta route-metrics-save:disabled')
    x.exec('203-offloading alpha offloading:off')
    x.exec('203-offloading beta offloading:off')

    x.exec('004-kill alpha')
    x.exec('004-kill beta')
    x.exec('004-kill koppa')

    x.exec('005-network setup:dumbbell alpha beta')

    x.exec('204-netem-cmd koppa control:partial change:add to-network:red command:"rate 160kbit limit 50"')
    x.exec('204-netem-cmd koppa control:partial change:add to-network:blue command:"rate 160kbit limit 50"')

    x.exec('101-tcpdump alpha id:10 mode:start filter:"tcp and port 30000"')
    x.exec('101-tcpdump beta id:11 mode:start filter:"tcp and port 30000"')

    x.exec('104-ipproof alpha sink:beta id:12 ipproof-client:/opt/ipproof/unix/ipproof-client ipproof-server:/opt/ipproof/unix/ipproof-server server-port:30000 transfer-size:1048576')

    x.exec('102-wait-for-id-completion interval_time:5 alpha:12')

    x.exec('101-tcpdump alpha id:10 mode:stop local-file-name:"./campaigns/003-del-acks/dumps/1_alpha.pcap"')
    x.exec('101-tcpdump beta id:11 mode:stop local-file-name:"./campaigns/003-del-acks/dumps/1_beta.pcap"')

    x.exec('004-kill alpha')
    x.exec('004-kill beta')
    x.exec('004-kill koppa')

    x.exec('005-network setup:dumbbell alpha beta')

    x.exec('202-ip-options alpha quickack:on min-rto:1ms')
    x.exec('202-ip-options beta quickack:on min-rto:1ms')

    x.exec('204-netem-cmd koppa control:partial change:add to-network:red command:"rate 160kbit limit 50"')
    x.exec('204-netem-cmd koppa control:partial change:add to-network:blue command:"rate 160kbit limit 50"')

    x.exec('101-tcpdump alpha id:20 mode:start filter:"tcp and port 30000"')
    x.exec('101-tcpdump beta id:21 mode:start filter:"tcp and port 30000"')

    x.exec('104-ipproof alpha sink:beta id:22 ipproof-client:/opt/ipproof/unix/ipproof-client ipproof-server:/opt/ipproof/unix/ipproof-server server-port:30000 transfer-size:1048576')

    x.exec('102-wait-for-id-completion interval_time:5 alpha:22')

    x.exec('101-tcpdump alpha id:20 mode:stop local-file-name:"./campaigns/003-del-acks/dumps/2_alpha.pcap"')
    x.exec('101-tcpdump beta id:21 mode:stop local-file-name:"./campaigns/003-del-acks/dumps/2_beta.pcap"')

    print(tt.update_campaign_runtime()[0])
