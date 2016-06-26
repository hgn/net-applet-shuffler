
import time


AMOUNT_TRIES = 3


def main(x, conf, args):
    if not len(args) > 0:
        x.p.err("no hostname argument given, like \"alpha\" "
                "(can be looked up in conf.json)\n")
        return False

    hostname = args[0]
    ip = conf.get_data_ip(hostname)
    for _ in range(0, AMOUNT_TRIES):
        ok = x.ping(ip)
        if ok:
            return True
        else:
            time.sleep(1)
    return False
