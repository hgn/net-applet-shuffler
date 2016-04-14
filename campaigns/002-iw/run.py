
CAMPAIGN_LENGTH = 502


def main(x):

    print('Starting campaign 002-iw')
    #iw_value_list = [4, 10, 20]
    #print('Running iw-value tests for iw-values {}'.format(str(iw_value_list)))

    for current_value in range(1, 21):
        iw_value = str(current_value)

    #for iw_value_list_position in range(0, len(iw_value_list)):
        #iw_value = str(iw_value_list[iw_value_list_position])
        print('Current iw-value tested: {}'.format(iw_value))

        x.exec('001-alive alpha')
        x.exec('001-alive beta')
        x.exec('001-alive koppa')

        x.exec('002-save-sysctls alpha')
        x.exec('002-save-sysctls beta')
        x.exec('002-save-sysctls koppa')

        x.exec('003-restore-sysctls alpha')
        x.exec('003-restore-sysctls beta')
        x.exec('003-restore-sysctls koppa')

        x.exec('007-kill alpha')
        x.exec('007-kill beta')
        x.exec('007-kill koppa')

        x.exec('009-network setup:indirect alpha beta')

        x.exec('102-tcp-route-metrics-save alpha route-metrics-save:disabled')
        x.exec('102-tcp-route-metrics-save beta route-metrics-save:disabled')
        x.exec('102-tcp-route-metrics-save koppa route-metrics-save:disabled')

        x.exec('105-offloading alpha offloading:off')
        x.exec('105-offloading beta offloading:off')

        x.exec('104-netem-cmd koppa control:part change:add to-network:red command:"rate 10kbit"')
        x.exec('104-netem-cmd koppa control:part change:add to-network:blue command:"rate 10kbit"')

        x.exec('101-tcp-iw alpha initcwnd:{} initrwnd:20'.format(iw_value))

        x.exec('006-tcpdump beta id:20 mode:start filter:"tcp and dst port 30000"')

        # test transfer
        x.exec('005-netperf alpha sink:beta id:21 source_port:20000 sink_port:30000 flow_length:-30000 flow_offset:1 netserver:29999')

        x.exec('008-wait-for-completion interval_time:2 alpha:20')

        x.exec('006-tcpdump beta id:20 mode:stop local-file-name:"./iw/iw_{}.pcap"'.format(iw_value))

    # reset offloading
    x.exec('105-offloading alpha offloading:on')
    x.exec('105-offloading beta offloading:on')
