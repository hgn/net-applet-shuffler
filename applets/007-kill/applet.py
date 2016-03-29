
def clean_directory(x, host_ip, host_user):
    x.ssh.exec(host_ip, host_user, "rm -fr /tmp/net-applet-shuffler/*")
    return True


def clean_service(x, host_ip, host_user, service_name):
    stdout = x.ssh.exec(host_ip, host_user, "pgrep {}".format(service_name))
    # iter through all pids
    for service_pid in stdout[0].decode("utf-8").splitlines():
        # try to end gracefully
        _, _, exit_code = x.ssh.exec(host_ip, host_user, "kill -2 {"
                "}".format(service_pid))
        # process MUST be kill
        if exit_code != 0:
            x.ssh.exec(host_ip, host_user, "kill {}".format(service_pid))

    return True


def main(x, conf, args):
    if not len(args) == 1:
        x.p.msg("wrong usage. use: [hostname]")
        return False

    # retrieve host information
    host_name = args[0]
    host_ip = conf.get_ip(host_name, 0)
    host_user = conf.get_user(host_name)

    #x.p.msg("cleaning up host {}\n".format(host_name))
    # 1. directory cleanup of /tmp/net-applet-shuffler/
    clean_directory(x, host_ip, host_user)
    # 2. netserver cleanup
    clean_service(x, host_ip, host_user, "netserver")
    # 3. tcpdump cleanup
    clean_service(x, host_ip, host_user, "tcpdump")
    # 4. netperf cleanup
    clean_service(x, host_ip, host_user, "netperf")

    return True
