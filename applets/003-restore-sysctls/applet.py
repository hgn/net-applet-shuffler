def main(x, conf, args):

    if not len(args) > 0:
        x.p.msg("no hostname argument given, like alpha\n")
        return False

    hostname = args[0]
    x.p.msg("restoring sysctl from /tmp/sysctl.save at host {}\n".format(hostname))

    ip = conf['boxes'][hostname]["interfaces"][0]['ip-address']
    user = conf['boxes'][hostname]['user']

    # check if a backup sysctl.save file exists
    # x.ssh.exec execute at ip with sudo
    stdout, stderr, exit_code = x.ssh.exec(ip, user, "test -f /tmp/sysctl.save")
    if exit_code != 0:
        x.p.msg("there is no sysctl.save backup which could be restored")
		# return true because it is not failure
        return False
    # there should be no failure here
    x.ssh.exec(ip, user, "sysctl -p/tmp/sysctl.save")

    return True
