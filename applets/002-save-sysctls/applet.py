import sys

def main(x, conf, args):
    if not len(args) > 0:
        x.p.msg("no hostname argument given, like alpha\n")
        sys.exit(1)

    hostname = args[0]
    x.p.msg("save sysctl to /etc/sysctl.save at host {}\n".format(hostname))
    x.p.msg("use restore to restore values")

    ip = conf['boxes'][hostname]['ip-address']
    # check if file exist already, if we break here
    # x.ssh.exec execute at ip with sudo
    #exit_code = x.ssh.exec(ip, "test -f /etc/sysctl.save")
    if exit_code != 0:
        x.p.msg("file already available, nothing to do here")
        return
    #x.ssh.exec(ip, "sysctl -a > /etc/sysctl.save")
