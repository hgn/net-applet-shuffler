
import sys

def main(x, conf, args):
    if not len(args) > 0:
        x.p.msg("no hostname argument given, like alpha\n")
        sys.exit(1)

    hostname = args[0]
    ip = conf['boxes'][hostname]['ip-address']
    ok = x.ping(ip)
    if not ok:
        return False
    return True
