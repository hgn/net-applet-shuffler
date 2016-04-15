
def main(x, conf, args):

    if not len(args) > 0:
        x.p.msg("no hostname argument given, like alpha\n")
        return False

    hostname = args[0]
    ip = conf.get_control_ip(hostname)
    user = conf.get_user(hostname)
    # check if a backup sysctl.save file exists
    exit_code = x.ssh.exec(ip, user, "test -f /tmp/sysctl.save")
    if exit_code != 0:
        x.p.err("error: no sysctl.save backup found on {}\n".format(hostname))
        return False
    # there should be no failure here
    exit_code = x.ssh.exec(ip, user, "sysctl -p /tmp/sysctl.save")
    if exit_code != 0:
        x.p.err("error: sysctls could not be restored on {}\n".format(hostname))
        return False

    return True
