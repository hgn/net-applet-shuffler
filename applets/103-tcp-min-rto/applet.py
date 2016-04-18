# usage: exec 103-tcp-min-rto [host] min-rto:[time]
# notes:
# [time] can be in sec and ms e.g. (1s, 200ms, 0.5ms -> 1ms)
# this does not affect ongoing open connections
# to check, open a new tcp connection (e.g. ssh)
# use "ip r s" and "ss -i" to verify


def set_rto(x, dic):
    rto_set_command = "ip route change default via {} dev {} rto_min {}"\
        .format(dic["default_route_data"], dic["iface_data"], dic["min_rto"])
    exit_code = x.ssh.exec(dic["ip_control"], dic["user"],
                           rto_set_command)
    if exit_code != 0:
        x.p.err("error: min rto could not be set\n")
        return False

    return True


def main(x, conf, args):
    if not len(args) == 2:
        x.p.err("wrong usage. use: [host] min-rto:[time]\n")
        return False
    # arguments dictionary
    dic = dict()
    try:
        dic["host_name"] = args[0]
        dic["min_rto"] = args[1].split(":")[1]
    except IndexError:
        x.p.err("error: wrong usage\n")
        return False
    dic["user"] = conf.get_user(dic["host_name"])
    dic["ip_control"] = conf.get_control_ip(dic["host_name"])
    dic["iface_data"] = conf.get_data_iface_name(dic["host_name"])
    dic["default_route_data"] = conf.get_data_default_route(dic["host_name"])
    # manipulate rto
    if not set_rto(x, dic):
        return False
    return True
