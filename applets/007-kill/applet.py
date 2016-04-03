
def clean_directory(x, host_name, host_user, host_ip):
    _, _, exit_code = x.ssh.exec(host_ip, host_user,
                                 "rm -fr /tmp/net-applet-shuffler/*")
    if exit_code != 0:
        x.p.msg("error: cleaning up {}'s /tmp/net-applet-shuffler/\n"
                .format(host_name))
        return False
    return True


def clean_service(x, host_name, host_user, host_ip, service_name):
    stdout, _, _ = x.ssh.exec(host_ip, host_user, "pgrep {}"
                              .format(service_name))
    # iter through all pids
    for service_pid in stdout.decode("utf-8").splitlines():
        # try to end gracefully
        _, _, exit_code = x.ssh.exec(host_ip, host_user, "kill -2 {}"
                                     .format(service_pid))
        # process MUST be kill
        if exit_code != 0:
            _, _, exit_code = x.ssh.exec(host_ip, host_user, "kill {}"
                                         .format(service_pid))
            if exit_code != 0:
                x.p.msg("error: {}'s {} could not be ended"
                        .format(host_name, service_name))
                return False

    return True


def main(x, conf, args):
    if not len(args) == 1:
        x.p.msg("wrong usage. use: [hostname]")
        return False

    # retrieve host information
    host_name = args[0]
    host_ip = conf.get_control_ip(host_name)
    host_user = conf.get_user(host_name)
    # 1. directory cleanup of /tmp/net-applet-shuffler/
    if not clean_directory(x, host_name, host_user, host_ip):
        return False
    # 2. netserver cleanup
    if not clean_service(x, host_name, host_user, host_ip, "netserver"):
        return False
    # 3. tcpdump cleanup
    if not clean_service(x, host_name, host_user, host_ip, "tcpdump"):
        return False
    # 4. netperf cleanup
    if not clean_service(x, host_name, host_user, host_ip, "netperf"):
        return False

    return True
