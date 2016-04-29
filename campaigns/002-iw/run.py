
import timetracker


def main(x):
    iw_list = [1, 2, 3, 4, 5, 6, 10, 12, 20]
    print('Starting campaign 002-iw')
    tt = timetracker.TimeTracker("002-iw")
    print(tt.get_campaign_runtime()[0])

    x.exec('001-alive alpha')
    x.exec('001-alive beta')
    x.exec('001-alive koppa')

    x.exec('002-save-sysctls alpha')
    x.exec('002-save-sysctls beta')
    x.exec('002-save-sysctls koppa')

    x.exec('203-offloading alpha offloading:off')
    x.exec('203-offloading beta offloading:off')

    print('###########################')
    print('###  Starting iw test   ###')
    print('###########################')
    for current_value in range(0, len(iw_list)):
        iw_value = str(iw_list[current_value])
        print('Current iw-value tested: {}'.format(iw_value))

        x.exec('003-restore-sysctls alpha')
        x.exec('003-restore-sysctls beta')
        x.exec('003-restore-sysctls koppa')
        x.exec('004-kill alpha')
        x.exec('004-kill beta')
        x.exec('004-kill koppa')
        x.exec('201-tcp-route-metrics alpha route-metrics-save:disabled')
        x.exec('201-tcp-route-metrics beta route-metrics-save:disabled')
        x.exec('201-tcp-route-metrics koppa route-metrics-save:disabled')

        x.exec('005-network setup:dumbbell alpha beta')

        x.exec('202-ip-options alpha initcwnd:{} initrwnd:{}'.format(iw_value, iw_value))
        x.exec('202-ip-options beta initcwnd:{} initrwnd:{}'.format(iw_value, iw_value))
        x.exec('205-tcp-window-mem koppa rmem_max:4194304 rmem_default:1048576 wmem_max:4194304 wmem_default:1048576 tcp_rmem_min:1048576 tcp_rmem_default:1048576 tcp_rmem_max:4194304 tcp_wmem_min:1048576 tcp_wmem_default:1048576 tcp_wmem_max:4194304')

        x.exec('101-tcpdump alpha id:10 mode:start filter:"tcp and port 30000"')
        x.exec('101-tcpdump beta id:11 mode:start filter:"tcp and port 30000"')

        x.exec('103-netperf alpha sink:beta id:12 source_port:20000 sink_port:30000 flow_length:-524288 flow_offset:1 netserver:29999')

        x.exec('102-wait-for-id-completion interval_time:2 alpha:12')

        x.exec('101-tcpdump alpha id:10 mode:stop local-file-name:"./campaigns/002-iw/dumps/alpha/iw_{}_alpha.pcap"'.format(iw_value))
        x.exec('101-tcpdump beta id:11 mode:stop local-file-name:"./campaigns/002-iw/dumps/alpha/iw_{}_beta.pcap"'.format(iw_value))

        print(tt.get_elapsed_runtime()[0])

    print(tt.get_remaining_runtime()[0])
    print(tt.add_poi("iw_test_done"))

    print('###############################################')
    print('###  Starting iw with delay 50ms and 80kbit ###')
    print('###############################################')
    for current_value in range(0, len(iw_list)):
        iw_value = str(iw_list[current_value])
        print('Current iw-value tested: {}'.format(iw_value))

        x.exec('003-restore-sysctls alpha')
        x.exec('003-restore-sysctls beta')
        x.exec('003-restore-sysctls koppa')
        x.exec('004-kill alpha')
        x.exec('004-kill beta')
        x.exec('004-kill koppa')
        x.exec('201-tcp-route-metrics alpha route-metrics-save:disabled')
        x.exec('201-tcp-route-metrics beta route-metrics-save:disabled')
        x.exec('201-tcp-route-metrics koppa route-metrics-save:disabled')

        x.exec('005-network setup:dumbbell alpha beta')

        x.exec('202-ip-options alpha initcwnd:{} initrwnd:{}'.format(iw_value, iw_value))
        x.exec('202-ip-options beta initcwnd:{} initrwnd:{}'.format(iw_value, iw_value))
        x.exec('205-tcp-window-mem alpha rmem_max:4194304 rmem_default:1048576 wmem_max:4194304 wmem_default:1048576 tcp_rmem_min:1048576 tcp_rmem_default:1048576 tcp_rmem_max:4194304 tcp_wmem_min:1048576 tcp_wmem_default:1048576 tcp_wmem_max:4194304')
        x.exec('205-tcp-window-mem beta rmem_max:4194304 rmem_default:1048576 wmem_max:4194304 wmem_default:1048576 tcp_rmem_min:1048576 tcp_rmem_default:1048576 tcp_rmem_max:4194304 tcp_wmem_min:1048576 tcp_wmem_default:1048576 tcp_wmem_max:4194304')
        x.exec('205-tcp-window-mem koppa rmem_max:4194304 rmem_default:1048576 wmem_max:4194304 wmem_default:1048576 tcp_rmem_min:1048576 tcp_rmem_default:1048576 tcp_rmem_max:4194304 tcp_wmem_min:1048576 tcp_wmem_default:1048576 tcp_wmem_max:4194304')
        x.exec('204-netem-cmd koppa control:full netem:"tc qdisc add dev enp0s25 root handle 1:0 netem delay 50ms"')
        x.exec('204-netem-cmd koppa control:full netem:"tc qdisc add dev enp0s25 parent 1:1 handle 10: tbf rate 80kbit buffer 12096 limit 12096"')
        x.exec('204-netem-cmd koppa control:full netem:"tc qdisc add dev enp3s2 root handle 1:0 netem delay 50ms"')
        x.exec('204-netem-cmd koppa control:full netem:"tc qdisc add dev enp3s2 parent 1:1 handle 10: tbf rate 80kbit buffer 12096 limit 12096"')

        x.exec('101-tcpdump alpha id:20 mode:start filter:"tcp and port 30000"')
        x.exec('101-tcpdump beta id:21 mode:start filter:"tcp and port 30000"')

        x.exec('103-netperf alpha sink:beta id:22 source_port:20000 sink_port:30000 flow_length:-524288 flow_offset:1 netserver:29999')

        x.exec('102-wait-for-id-completion interval_time:2 alpha:22')

        x.exec('101-tcpdump alpha id:20 mode:stop local-file-name:"./campaigns/002-iw/dumps/alpha/iw_{}_50ms_80kb_alpha.pcap"'.format(iw_value))
        x.exec('101-tcpdump beta id:21 mode:stop local-file-name:"./campaigns/002-iw/dumps/alpha/iw_{}_50ms_80kb_beta.pcap"'.format(iw_value))

        print(tt.get_elapsed_runtime()[0])

    print(tt.get_remaining_runtime()[0])
    print(tt.add_poi("iw_test_with_50ms_80kbit_done"))

    print('########################################')
    print('###  Starting iw test with 160kbit  ###')
    print('########################################')
    for current_value in range(0, len(iw_list)):
        iw_value = str(iw_list[current_value])
        print('Current iw-value tested: {}'.format(iw_value))

        x.exec('003-restore-sysctls alpha')
        x.exec('003-restore-sysctls beta')
        x.exec('003-restore-sysctls koppa')
        x.exec('004-kill alpha')
        x.exec('004-kill beta')
        x.exec('004-kill koppa')
        x.exec('201-tcp-route-metrics alpha route-metrics-save:disabled')
        x.exec('201-tcp-route-metrics beta route-metrics-save:disabled')
        x.exec('201-tcp-route-metrics koppa route-metrics-save:disabled')

        x.exec('005-network setup:dumbbell alpha beta')

        x.exec('205-tcp-window-mem alpha rmem_max:4194304 rmem_default:1048576 wmem_max:4194304 wmem_default:1048576 tcp_rmem_min:1048576 tcp_rmem_default:1048576 tcp_rmem_max:4194304 tcp_wmem_min:1048576 tcp_wmem_default:1048576 tcp_wmem_max:4194304')
        x.exec('205-tcp-window-mem beta rmem_max:4194304 rmem_default:1048576 wmem_max:4194304 wmem_default:1048576 tcp_rmem_min:1048576 tcp_rmem_default:1048576 tcp_rmem_max:4194304 tcp_wmem_min:1048576 tcp_wmem_default:1048576 tcp_wmem_max:4194304')
        x.exec('205-tcp-window-mem koppa rmem_max:4194304 rmem_default:1048576 wmem_max:4194304 wmem_default:1048576 tcp_rmem_min:1048576 tcp_rmem_default:1048576 tcp_rmem_max:4194304 tcp_wmem_min:1048576 tcp_wmem_default:1048576 tcp_wmem_max:4194304')
        x.exec('204-netem-cmd koppa control:full netem:"tc qdisc add dev enp0s25 root handle 1:0 netem"')
        x.exec('204-netem-cmd koppa control:full netem:"tc qdisc add dev enp0s25 parent 1:1 handle 10: tbf rate 160kbit buffer 12096 limit 12096"')
        x.exec('204-netem-cmd koppa control:full netem:"tc qdisc add dev enp3s2 root handle 1:0 netem"')
        x.exec('204-netem-cmd koppa control:full netem:"tc qdisc add dev enp3s2 parent 1:1 handle 10: tbf rate 160kbit buffer 12096 limit 12096"')

        x.exec('202-ip-options alpha initcwnd:{} initrwnd:{}'.format(iw_value, iw_value))
        x.exec('202-ip-options beta initcwnd:{} initrwnd:{}'.format(iw_value, iw_value))

        x.exec('101-tcpdump alpha id:30 mode:start filter:"tcp and port 30000"')
        x.exec('101-tcpdump beta id:31 mode:start filter:"tcp and port 30000"')

        x.exec('103-netperf alpha sink:beta id:32 source_port:20000 sink_port:30000 flow_length:-524288 flow_offset:1 netserver:29999')

        x.exec('102-wait-for-id-completion interval_time:2 alpha:32')

        x.exec('101-tcpdump alpha id:30 mode:stop local-file-name:"./campaigns/002-iw/dumps/alpha/iw_{}_160kb_alpha.pcap"'.format(iw_value))
        x.exec('101-tcpdump beta id:31 mode:stop local-file-name:"./campaigns/002-iw/dumps/alpha/iw_{}_160kb_beta.pcap"'.format(iw_value))

        print(tt.get_elapsed_runtime()[0])

    print(tt.get_remaining_runtime()[0])
    print(tt.add_poi("iw_test_with_160kbit_done"))

    # reset qdiscs
    x.exec('204-netem-cmd koppa control:partial change:del to_network:red')
    x.exec('204-netem-cmd koppa control:partial change:del to_network:blue')

    # reset offloading
    x.exec('203-offloading alpha offloading:on')
    x.exec('203-offloading beta offloading:on')

    print(tt.update_campaign_runtime()[0])
