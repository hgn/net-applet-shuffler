# usage: exec 102-metrics-save [host] route-metrics-save:[enabled|disabled]
# Check success:
#  sysctl /net/ipv4/tcp_no_metrics_save


def set_metric_save(x, user, ip, route_metric):
    # 1. set route metric
    route_m = 0
    if route_metric == "disabled":
        route_m = 1
    metric_set_command = "sysctl -w /net/ipv4/tcp_no_metrics_save=\"{}\" " \
                         "".format(route_m)
    exit_code = x.ssh.exec(ip, user, metric_set_command)
    if exit_code != 0:
        x.p.err("error: route metric could not be set\n")
        return False
    # 2. flush route metric cache if metrics save shall be disabled
    if route_metric == "disabled":
        exit_code = x.ssh.exec(ip, user, "ip tcp_metrics flush")
        if exit_code != 0:
            x.p.err("error: route metric cache could not be flushed\n")
            return False

    return True


def main(x, conf, args):
    if not len(args) == 2:
        x.p.err("wrong usage. use: [host] "
                "route-metrics-save:[enabled|disabled]\n")
        return False
    # arguments dictionary
    dic = dict()
    try:
        dic["host_name"] = args[0]
        dic["m_save"] = args[1].split(":")[1]
    except IndexError:
        x.p.err("error: wrong usage\n")
        return False
    dic["user"] = conf.get_user(dic["host_name"])
    dic["ip_control"] = conf.get_control_ip(dic["host_name"])
    # manipulate metric
    if not set_metric_save(x, dic["user"], dic["ip_control"], dic["m_save"]):
        return False
    return True
