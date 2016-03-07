
import sys

def main(x, conf, args):
    if not len(args) > 0:
        x.p.msg("no hostname argument given, like \"alpha\" (can be looked up in conf.json)\n")
        return False

    hostname = args[0]
    ip = conf['boxes'][hostname]['interfaces'][0]['ip-address']
    ok = x.ping(ip)
    if not ok:
        return False
    return True
