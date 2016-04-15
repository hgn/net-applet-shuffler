
def main(x, conf, args):
    if not len(args) > 0:
        x.p.msg("no hostname argument given, like alpha\n")
        return False

    hostname = args[0]
    ip = conf.get_control_ip(hostname)
    user = conf.get_user(hostname)
    # check if file exist already, if we break here
    # the following four lines are probably obsolete
    exit_code = x.ssh.exec(ip, user, "test -f /tmp/sysctl.save")
    if exit_code == 0:
        x.p.msg("file already available, nothing to do here\n")
        # return true because it is not failure
        return True
    # there should be no failure here
    _, _, exit_code = x.ssh.exec_verbose(ip, user, "sysctl -a > /tmp/"
                                                   "sysctl.save 2>/dev/null")
    if exit_code != 0:
        x.p.err("error: sysctls could not be saved on {}\n".format(hostname))
        return False
    
    return True
