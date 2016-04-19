# usage: exec [host] offloading:[on|off]
#
# Check success:
#  - sudo ethtool -k [device_name]
#
# Examples:
#  - sudo ethtool -K enp4s0 tso off ufo off gso off gro off lro off
#  - exec-applet 105-offloading alpha offloading:off
#
# Hints:
#  - "Cannot change [...]" messages probably mean that the value can not be
#    changed (is fixed)
#  - ethtool feedbacks fail when nothing was changed


def print_usage(x):
    x.p.msg("\n usage:\n", False)
    x.p.msg(" - exec 105-offloading [host] offloading:\"[on|off]\"\n", False)
    x.p.msg("\n check success:\n", False)
    x.p.msg(" - ethtool -k [interface]\n", False)
    x.p.msg("\nexample:\n", False)
    x.p.msg(" - exec-applet 105-offloading alpha offloading:on\n", False)


def set_offloading(x, conf, dic):
    device_list = conf.get_all_data_iface_names(dic["host"])
    for device in device_list:
        cmd = str()
        if dic["offloading"] == "on":
            cmd = "ethtool -K {} tso on ufo on gso on gro on lro on"\
                .format(device)
        elif dic["offloading"] == "off":
            cmd = "ethtool -K {} tso off ufo off gso off gro off lro off"\
                .format(device)
        else:
            x.p.err("error: wrong usage\n")
            return False
        # unfortunately, error handling does not work, since ethtool's feedback
        # fails when nothing was done
        x.ssh.exec(dic["ip_control"], dic["user"], cmd)

    return True


def main(x, conf, args):
    if "?" in args:
        print_usage(x)
        return False
    if not len(args) >= 2:
        x.p.err("error: wrong usage\n")
        return False

    # arguments dictionary
    dic = dict()
    try:
        dic["host"] = args[0]
        dic["offloading"] = args[1].split(":")[1]
    except IndexError:
        x.p.err("error: wrong usage\n")
        return False

    dic["user"] = conf.get_user(dic["host"])
    dic["ip_control"] = conf.get_control_ip(dic["host"])

    return set_offloading(x, conf, dic)
