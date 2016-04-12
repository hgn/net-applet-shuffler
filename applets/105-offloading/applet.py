# usage: exec [host] command:"[command]"
#
# Check success:
#  - sudo ethtool -k [device_name]
#
# Examples:
#  - sudo ethtool -K enp4s0 tso off ufo off gso off gro off lro off
#  - exec-applet 105-offloading alpha command:"tso off ufo off gso off gro off
#    lro off"
#
# Hints:
#  - "Cannot change [...]" messages probably mean that the value can not be
#    changed (is fixed)


def print_usage(x):

    x.p.msg("\n usage:\n", False)
    x.p.msg(" - exec 105-offloading [host] command:\"[command]\"\n", False)
    x.p.msg("\n check success:\n", False)
    x.p.msg(" - ethtool -k [interface]\n", False)
    x.p.msg("\nexample:\n", False)
    x.p.msg(" - exec-applet 105-offloading alpha command:"
            "\"tso off ufo off gso off gro off lro off\"\n",
            False)

    return False


def set_offloading(x, conf, dic):

    device_list = conf.get_all_test_iface_names(dic["host"])
    for device in device_list:
        cmd = "ethtool -K {} {}".format(device, dic["cmd"])
        _, _, exit_code = x.ssh.exec(dic["ip_control"], dic["user"], cmd)
        if exit_code != 0:
            x.p.err("error: offloading could not be set for host {} device {}\n"
                    .format(dic["host"], device))
            x.p.err("failed cmd: \"{}\"".format(cmd))
            return False

    return True


def main(x, conf, args):

    if "?" in args:
        return print_usage(x)
    if not len(args) >= 2:
        x.p.err("error: wrong usage\n")
        return False

    # arguments dictionary
    dic = dict()
    try:
        dic["host"] = args[0]
        position = 1
        command_str = args[1].split(":")[1]
        try:
            while True:
                position += 1
                command_str += " " + args[position]
        except IndexError:
            pass
        dic["cmd"] = command_str.strip("\"")
    except IndexError:
        x.p.err("error: wrong usage\n")
        return False

    dic["user"] = conf.get_user(dic["host"])
    dic["ip_control"] = conf.get_control_ip(dic["host"])

    return set_offloading(x, conf, dic)
