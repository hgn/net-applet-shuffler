"""Applet for setting ip options: tcp windows, tcp quickack

Usage:
exec 101-ip-options [host] [initcwnd:[number]] [initrwnd:[number]]
 [quickack:[on|off]]

Check Success:
ip r s

Examples:
- exec-applet 101-ip-options alpha initcwnd:12 quickack:on
- exec-applet 101-ip-options beta initrwnd:4
- exec-applet 101-ip-options beta initcwnd:20 initrwnd:20 quickack:on

Hints:
- if ip options are missing, they probably should be added here
"""


def print_usage(x):
    x.p.msg("\n usage:\n", False)
    x.p.msg(" - exec 101-ip-options [host] [initcwnd:[number]] "
            "[initrwnd:[number]] [quickack:[on|off]]\n", False)
    x.p.msg("\n check success:\n", False)
    x.p.msg(" - ip r s\n", False)
    x.p.msg("\n examples:\n", False)
    x.p.msg(" - exec-applet 101-ip-options alpha initcwnd:12 initrwnd:12 "
            "quickack:on\n", False)
    x.p.msg(" - exec-applet 101-ip-options beta quickack:on initcwnd:12\n\n",
            False)


def print_wrong_usage(x):
    x.p.err("error: wrong usage\n")
    x.p.err("use: [host] [initcwnd:[number]] [initrwnd:[number]] "
            "[quickack:[on|off]]\n")


def set_ip_options(x, dic, options):
    cmd = "ip route change default via {} proto static dev {}{}".format(
        dic["default_route_data"], dic["interface_data"], options)
    exit_code = x.ssh.exec(dic["ip_control"], dic["user"], cmd)
    if exit_code != 0:
        x.p.err("error: ip option(s) could not be set\n")
        x.p.err("failed cmd: {}\n".format(cmd))
        return False

    return True


def main(x, conf, args):
    if "?" in args:
        print_usage(x)
        return False
    if not len(args) >= 2:
        print_wrong_usage(x)
        return False
    # arguments dictionary
    dic = dict()
    options = str()
    try:
        dic["host_name"] = args[0]
        args.remove(dic["host_name"])
        for argument in args:
            if argument.split(":")[0] == "initcwnd":
                options += " initcwnd {}".format(argument.split(":")[1])
            elif argument.split(":")[0] == "initrwnd":
                options += " initrwnd {}".format(argument.split(":")[1])
            elif argument.split(":")[0] == "quickack":
                if argument.split(":")[1] == "on":
                    options += " quickack 1"
                elif argument.split(":")[1] == "off":
                    options += " quickack 0"
                else:
                    print_wrong_usage(x)
                    return False
            else:
                print_wrong_usage(x)
                return False
    except IndexError:
        print_wrong_usage(x)
        return False
    # retrieve host information from conf
    dic["user"] = conf.get_user(dic["host_name"])
    dic["ip_control"] = conf.get_control_ip(dic["host_name"])
    dic["default_route_data"] = conf.get_data_default_route(dic["host_name"])
    dic["interface_data"] = conf.get_data_iface_name(dic["host_name"])
    # set ip options
    if not set_ip_options(x, dic, options):
        return False
    return True
