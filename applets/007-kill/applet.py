
def clean_directory(x, host_ip, host_user):

    x.ssh.exec(host_ip, host_user, "rm -fr /tmp/net-applet-shuffler/*")

    return True


def clean_service(x, host_ip, host_user, service_name):

    stdout = x.ssh.exec(host_ip, host_user, "pgrep {}".format(service_name))

    # iter through all pids
    for service_pid in stdout[0].decode("utf-8").splitlines():

        # try to end gracefully
        stdout, stderr, exit_code = x.ssh.exec(host_ip, host_user, "kill -2 {"
                "}".format(service_pid))

        # process MUST be kill
        if exit_code != 0:
            x.ssh.exec(host_ip, host_user, "kill {}".format(service_pid))

    return True


def main(x, conf, args):

    if not len(args) == 1:
        x.p.msg("wrong usage. use: host:[name]")

        return False

    # retrieve host information
    host_name = args[0].split(":")[1]
    host_ip = conf['boxes'][host_name]["interfaces"][0]['ip-address']
    host_user = conf['boxes'][host_name]['user']

    x.p.msg("cleaning up host {}".format(host_name))
    # 1. directory cleanup of /tmp/net-applet-shuffler/
    clean_directory(x, host_ip, host_user)
    # 2. netserver cleanup
    clean_service(x, host_ip, host_user, "netserver")
    # 3. tcpdump cleanup
    clean_service(x, host_ip, host_user, "tcpdump")

    return True
