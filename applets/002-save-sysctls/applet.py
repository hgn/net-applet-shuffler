
def main(x, conf, args):
    if not len(args) > 0:
        x.p.msg("no hostname argument given, like alpha\n")
        return False

    hostname = args[0]
    #x.p.msg("save sysctls to /tmp/sysctl.save at host {}\n".format(hostname))

    ip = conf.get_control_ip(hostname)
    user = conf.get_user(hostname)
    # check if file exist already, if we break here
    # the following three lines are probably obsolete
    _, _, exit_code = x.ssh.exec(ip, user, "test -f /tmp/sysctl.save")
    if exit_code == 0:
        x.p.msg("file already available, nothing to do here\n")
        # return true because it is not failure
        return True
    # there should be no failure here
    x.ssh.exec(ip, user, "sysctl -a > /tmp/sysctl.save")
    
    return True
