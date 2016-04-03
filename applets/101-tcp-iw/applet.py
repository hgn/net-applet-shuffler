# usage: exec 101-tcp-iw [host]  initcwnd:[number] initrwnd:[number]


def set_iw(x, arg_d):
    iw_set_command = "ip route change default via {} proto static dev {} init" \
                     "cwnd {} initrwnd {}".format(arg_d["default_route_test"],
                                                  arg_d["interface_test"],
                                                  arg_d["initcwnd"],
                                                  arg_d["initrwnd"])
    _, _, exit_code = x.ssh.exec(arg_d["ip_control"], arg_d["host_user"],
                                 iw_set_command)
    if exit_code != 0:
        return False
    return True


def main(x, conf, args):
    if not len(args) == 3:
        x.p.msg("wrong usage. use: [host] initcwnd:[number] initrwnd:[number]"
                "\n")
        return False

    # arguments dictionary
    arg_d = dict()
    try:
        arg_d["host_name"] = args[0]
        # initial sending congestion window
        # ss -nli | grep cwnd
        # probably 10
        arg_d["initcwnd"] = args[1].split(":")[1]
        # advertised receive congestion window
        arg_d["initrwnd"] = args[2].split(":")[1]
    except IndexError:
        x.p.msg("error: wrong usage\n")
        return False
    arg_d["host_user"] = conf.get_user(arg_d["host_name"])
    arg_d["ip_control"] = conf.get_control_ip(arg_d["host_name"])
    arg_d["default_route_test"] = conf.get_test_default_route(arg_d["host_name"])
    arg_d["interface_test"] = conf.get_test_iface_name(arg_d["host_name"])
    # set iw on host
    if not set_iw(x, arg_d):
        return False
    return True

# use sysctl: -n net.ipv4.tcp_wmem (e.g. 4096 16384 419394)
# net.ipv4.tcp_rmem
# tcp slow start (tcp_slow_start_after_idle)?
