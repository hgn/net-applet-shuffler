
import timetracker

CAMPAIGN_NAME = "010-rto-rfc"

# campaign settings
AMOUNT_RUNS = 10
AMOUNT_PACKETS = [12, 16, 32, 64]
LOSS_RATE = 1

TRANSFER_SIZE = 1448 * AMOUNT_PACKETS
NETEM_CMD = "delay 50ms 2.5ms rate 10000kbit limit 44 loss {}%".format(LOSS_RATE)
SUB_PATH = "campaigns/{}".format(CAMPAIGN_NAME)


def main(x):
    print('Starting campaign {}'.format(CAMPAIGN_NAME))
    tt = timetracker.TimeTracker("{}".format(CAMPAIGN_NAME))
    print(tt.get_campaign_runtime()[0])

    x.exec('001-alive alpha')
    x.exec('001-alive gamma')
    x.exec('001-alive beta')
    x.exec('001-alive koppa')

    x.exec('002-save-sysctls gamma')
    x.exec('002-save-sysctls beta')
    x.exec('002-save-sysctls koppa')

    x.exec('203-offloading gamma offloading:off')
    x.exec('203-offloading beta offloading:off')

    x.exec('003-restore-sysctls gamma')
    x.exec('003-restore-sysctls beta')
    x.exec('003-restore-sysctls koppa')
    x.exec('201-tcp-route-metrics gamma route-metrics-save:disabled')
    x.exec('201-tcp-route-metrics beta route-metrics-save:disabled')
    x.exec('201-tcp-route-metrics koppa route-metrics-save:disabled')

    x.exec('005-network setup:dumbbell gamma beta')

    for run in range(1, (AMOUNT_RUNS + 1), 1):

        print(tt.get_elapsed_runtime()[0])
        print("Current run: {}".format(run))
        x.exec('004-kill gamma')
        x.exec('004-kill beta')
        x.exec('004-kill koppa')

        x.exec('101-tcpdump gamma id:10 mode:start filter:"tcp and port 30000"')
        x.exec('101-tcpdump beta id:11 mode:start filter:"tcp and port 30000"')

        x.exec('204-netem-cmd koppa control:partial change:add to-network:blue command:"{}"'.format(NETEM_CMD))
        x.exec('204-netem-cmd koppa control:partial change:add to-network:red command:"{}"'.format(NETEM_CMD))

        x.exec('104-ipproof gamma sink:beta id:12 ipproof-client:/opt/ipproof/unix/ipproof-client ipproof-server:/opt/ipproof/unix/ipproof-server server-port:30000 transfer-size:{}'.format(TRANSFER_SIZE))

        x.exec('102-wait-for-id-completion interval_time:5 gamma:12')

        x.exec('008-export-campaign gamma campaign_name:"{}" path:"./{}/{}/setup.save'.format(CAMPAIGN_NAME, SUB_PATH, run))
        x.exec('101-tcpdump gamma id:10 mode:stop local-file-name:"./{}/{}/dump_gamma.pcap"'.format(SUB_PATH, run))
        x.exec('101-tcpdump beta id:11 mode:stop local-file-name:"./{}/{}/dump_beta.pcap"'.format(SUB_PATH, run))

    # reset offloading
    x.exec('203-offloading gamma offloading:on')
    x.exec('203-offloading beta offloading:on')
    # reset qdiscs
    x.exec('004-kill koppa')

    print(tt.update_campaign_runtime()[0])
