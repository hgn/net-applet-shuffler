
def clean_directory(x, host_name, host_user, host_ip):
    exit_code = x.ssh.exec(host_ip, host_user,
                           "rm -fr /tmp/net-applet-shuffler/*")
    if exit_code != 0:
        x.p.err("error: cleaning up {}'s /tmp/net-applet-shuffler/\n"
                .format(host_name))
        return False
    return True


def clean_qdiscs(x, conf, host_name, host_user, host_ip):
    interface_list = conf.get_all_data_iface_names(host_name)
    for interface in interface_list:
        cmd = "tc qdisc del dev {} root netem".format(interface)
        # try, since this should only work for an active qdisc
        x.ssh.exec(host_ip, host_user, cmd)
    return True


def clean_service(x, host_name, host_user, host_ip, service_name):
    stdout, _, _ = x.ssh.exec_verbose(host_ip, host_user,
                                      "pgrep {}".format(service_name))
    # iter through all pids
    for service_pid in stdout.decode("utf-8").splitlines():
        # try to end gracefully
        exit_code = x.ssh.exec(host_ip, host_user,
                               "kill -2 {}".format(service_pid))
        # process MUST be kill
        if exit_code != 0:
            exit_code = x.ssh.exec(host_ip, host_user,
                                   "kill {}".format(service_pid))
            if exit_code != 0:
                x.p.err("error: {}'s {} could not be ended"
                        .format(host_name, service_name))
                return False

    return True


def main(x, conf, args):
    if not len(args) == 1:
        x.p.err("wrong usage. use: [hostname]")
        return False

    # retrieve host information
    host_name = args[0]
    host_ip = conf.get_control_ip(host_name)
    host_user = conf.get_user(host_name)
    # 1. directory cleanup of /tmp/net-applet-shuffler/
    if not clean_directory(x, host_name, host_user, host_ip):
        return False
    # 2. tcpdump cleanup
    if not clean_service(x, host_name, host_user, host_ip, "tcpdump"):
        return False
    # 3. netserver cleanup
    if not clean_service(x, host_name, host_user, host_ip, "netserver"):
        return False
    # 4. netperf cleanup
    if not clean_service(x, host_name, host_user, host_ip, "netperf"):
        return False
    # 5. ipproof cleanup
    if not clean_service(x, host_name, host_user, host_ip, "ipproof"):
        return False
    # 6. qdiscs cleanup
    clean_qdiscs(x, conf, host_name, host_user, host_ip)

    return True
