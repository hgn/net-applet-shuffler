
import timetracker


def main(x):

    print('Starting campaign 002-iw')
    tt = timetracker.TimeTracker("002-iw")
    print(tt.get_campaign_runtime()[0])

    #iw_value_list = [4, 10, 20]
    #print('Running iw-value tests for iw-values {}'.format(str(iw_value_list)))

    x.exec('001-alive alpha')
    x.exec('001-alive beta')
    x.exec('001-alive koppa')

    # restore default sysctls and save it when initial
    x.exec('002-save-sysctls alpha')
    x.exec('002-save-sysctls beta')
    x.exec('002-save-sysctls koppa')
    x.exec('003-restore-sysctls alpha')
    x.exec('003-restore-sysctls beta')
    x.exec('003-restore-sysctls koppa')

    x.exec('105-offloading alpha offloading:off')
    x.exec('105-offloading beta offloading:off')

    for current_value in range(1, 21):
        iw_value = str(current_value)

        #for iw_value_list_position in range(0, len(iw_value_list)):
        #iw_value = str(iw_value_list[iw_value_list_position])
        print('Current iw-value tested: {}'.format(iw_value))

        # stop running interfering programs and delete possible qdiscs
        x.exec('007-kill alpha')
        x.exec('007-kill beta')
        x.exec('007-kill koppa')

        x.exec('009-network setup:dumbbell alpha beta')

        x.exec('104-netem-cmd koppa control:partial change:add to_network:red command:"delay 100ms"')
        x.exec('104-netem-cmd koppa control:partial change:add to_network:blue command:"delay 100ms"')

        x.exec('102-tcp-route-metrics alpha route-metrics-save:disabled')
        x.exec('102-tcp-route-metrics beta route-metrics-save:disabled')
        x.exec('102-tcp-route-metrics koppa route-metrics-save:disabled')

        #x.exec('104-netem-cmd koppa control:partial change:add to-network:red command:"rate 10kbit"')
        #x.exec('104-netem-cmd koppa control:partial change:add to-network:blue command:"rate 10kbit"')

        x.exec('101-tcp-iw alpha initcwnd:{} initrwnd:{}'.format(iw_value, iw_value))
        x.exec('101-tcp-iw beta initcwnd:{} initrwnd:{}'.format(iw_value, iw_value))

        x.exec('006-tcpdump beta id:20 mode:start filter:"tcp and port 30000"')

        # test transfer
        x.exec('005-netperf alpha sink:beta id:21 source_port:20000 sink_port:30000 flow_length:-30000 flow_offset:1 netserver:29999')

        x.exec('008-wait-for-id-completion interval_time:2 alpha:21')

        x.exec('006-tcpdump beta id:20 mode:stop local-file-name:"./campaigns/002-iw/dumps/iw_{}.pcap"'.format(iw_value))

        print(tt.get_elapsed_runtime()[0])
        print(tt.get_remaining_runtime()[0])

    # reset offloading
    x.exec('105-offloading alpha offloading:on')
    x.exec('105-offloading beta offloading:on')

    # reset qdiscs
    x.exec('104-netem-cmd koppa control:partial change:del to_network:red')
    x.exec('104-netem-cmd koppa control:partial change:del to_network:blue')

    print(tt.update_campaign_runtime()[0])
