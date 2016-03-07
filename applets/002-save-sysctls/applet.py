import sys

def main(x, conf, args):
    if not len(args) > 0:
        x.p.msg("no hostname argument given, like alpha\n")
        return False

    hostname = args[0]
    x.p.msg("save sysctl to /tmp/sysctl.save at host {}\n".format(hostname))
    x.p.msg("use restore to restore values")

    ip = conf['boxes'][hostname]["interfaces"][0]['ip-address']
    user = conf['boxes'][hostname]['user']
    # check if file exist already, if we break here
    # x.ssh.exec execute at ip with sudo
    stdout, stderr, exit_code = x.ssh.execute(ip, user, "test -f /tmp/sysctl.save")
    if exit_code != 0:
        x.p.msg("file already available, nothing to do here")
		# return true because it is not failure
        return True
    # there should be no failure here
    x.ssh.execute(ip, user, "sysctl -a > /tmp/sysctl.save")
    
    return True
