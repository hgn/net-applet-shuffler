"""Applet for setting tcp sysctl window memory values
Usage:
exec 205-tcp-window-mem [host]
                        [rmem_max:[byte]]
                        [rmem_default:[byte]]
                        [wmem_max:[byte]]
                        [wmem_default:[byte]]
                        [window_scaling:[on|off]]
                        [tcp_rmem_min:[byte]]
                        [tcp_rmem_default:[byte]]
                        [tcp_rmem_max:[byte]]
                        [tcp_wmem_min:[byte]]
                        [tcp_wmem_default:[byte]]
                        [tcp_wmem_max:[byte]]

Check Success:
sysctl [/net/core/[option]|/net/ipv4/[option]]

Examples:
- exec-applet 205-tcp-window-mem alpha window_scaling:on rmem_max:12582912
 rmem_default:12582912
- exec-applet 205-tcp-window-mem beta window_scaling:on wmem_max:12582912
 wmem_default:12582912 tcp_rmem_min:12582912 tcp_rmem_default:12582912
 tcp_rmem_max:12582912

Hints:
- restoration is covered by restoring sysctls, e.g. 003-restore-sysctls or a
 reboot
"""


def print_usage(x):
    x.p.msg("\n 205-tcp-window-mem:\n", False)
    x.p.msg(" applet for setting tcp window memory values\n", False)
    x.p.msg("\n usage:\n", False)
    x.p.msg(" - exec 205-tcp-window-mem [host] "
            "[rmem_max:[byte]] "
            "[rmem_default:[byte]] "
            "[wmem_max:[byte]] "
            "[wmem_default:[byte]] "
            "[window_scaling:[on|off]] "
            "[tcp_rmem_min:[byte]] "
            "[tcp_rmem_default:[byte]] "
            "[tcp_rmem_max:[byte]] "
            "[tcp_wmem_min:[byte]] "
            "[tcp_wmem_default:[byte]] "
            "[tcp_wmem_max:[byte]]\n", False)
    x.p.msg("\n check success:\n", False)
    x.p.msg(" - sysctl [/net/core/[option]|/net/ipv4/[option]]\n", False)
    x.p.msg("\n examples:\n", False)
    x.p.msg(" - exec-applet 205-tcp-window-mem alpha window_scaling:on "
            "rmem_max:12582912 rmem_default:12582912\n", False)
    x.p.msg(" - exec-applet 205-tcp-window-mem beta window_scaling:on "
            "wmem_max:12582912 wmem_default:12582912 tcp_rmem_min:12582912 "
            "tcp_rmem_default:12582912 tcp_rmem_max:12582912\n", False)
    x.p.msg("\n hints:\n", False)
    x.p.msg(" - restoration is covered by restoring sysctls, e.g. "
            "003-restore-sysctls or a reboot\n\n", False)


def print_wrong_usage(x):
    x.p.err("error: wrong usage\n")
    x.p.err("use: [host] "
            "[rmem_max:[byte]] "
            "[rmem_default:[byte]] "
            "[wmem_max:[byte]] "
            "[wmem_default:[byte]] "
            "[window_scaling:[on|off]] "
            "[tcp_rmem_min:[byte]] "
            "[tcp_rmem_default:[byte]] "
            "[tcp_rmem_max:[byte]] "
            "[tcp_wmem_min:[byte]] "
            "[tcp_wmem_default:[byte]] "
            "[tcp_wmem_max:[byte]]\n")


def construct_tcp_mem_string(x, dic, tcp_mem_str, new_value_dict):
    cmd = "sysctl /net/ipv4/{}".format(tcp_mem_str)
    stdout, _, exit_code = x.ssh.exec_verbose(dic["ip_control"],
                                              dic["user"],
                                              cmd)
    if exit_code != 0:
        x.p.err("error: tcp window values could not retrieved from "
                "{}\n".format(dic["host_name"]))
        x.p.err("failed cmd: {}\n".format(cmd))
        return False
    # construct dict with read values
    constructed_dict = dict()
    stdout_decoded = stdout.decode("utf-8")
    string_value_side = stdout_decoded.split("=")[1]
    constructed_dict["0"] = string_value_side.split()[0]
    constructed_dict["1"] = string_value_side.split()[1]
    constructed_dict["2"] = string_value_side.split()[2]
    # now override with new values
    mem_str = str()
    for number in range(0, 3):
        if str(number) in new_value_dict:
            mem_str += new_value_dict[str(number)] + " "
        else:
            mem_str += constructed_dict[str(number)] + " "
    mem_str = mem_str.strip()
    return mem_str


def set_options(x, dic, options_dict, tcp_rmem_dict, tcp_wmem_dict):
    for option in options_dict:
        cmd = "sysctl -w {}=\"{}\"".format(option, options_dict[option])
        exit_code = x.ssh.exec(dic["ip_control"], dic["user"], cmd)
        if exit_code != 0:
            x.p.err("error: tcp window value could not be set\n")
            x.p.err("failed cmd: {}\n".format(cmd))
            return False
    if tcp_rmem_dict:
        value = construct_tcp_mem_string(x, dic, "tcp_rmem", tcp_rmem_dict)
        cmd = "sysctl -w /net/ipv4/tcp_rmem=\"{}\"".format(value)
        exit_code = x.ssh.exec(dic["ip_control"], dic["user"], cmd)
        if exit_code != 0:
            x.p.err("error: tcp rmem value could not be set\n")
            x.p.err("failed cmd: {}\n".format(cmd))
            return False
    if tcp_wmem_dict:
        value = construct_tcp_mem_string(x, dic, "tcp_wmem", tcp_rmem_dict)
        cmd = "sysctl -w /net/ipv4/tcp_wmem=\"{}\"".format(value)
        exit_code = x.ssh.exec(dic["ip_control"], dic["user"], cmd)
        if exit_code != 0:
            x.p.err("error: tcp wmem value could not be set\n")
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
    # dictionaries:
    dic = dict()
    options = dict()
    # tcp dicts, [0]: min, [1]: default, [2]: max, separated by whitespaces
    # these are also options, but can be handled more convenient like this
    tcp_rmem = dict()
    tcp_wmem = dict()
    try:
        dic["host_name"] = args[0]
        args.remove(dic["host_name"])
        for argument in args:
            key = argument.split(":")[0]
            value = argument.split(":")[1]
            if key == "rmem_max":
                options["/net/core/rmem_max"] = value
            elif key == "rmem_default":
                options["/net/core/rmem_default"] = value
            elif key == "wmem_max":
                options["/net/core/wmem_max"] = value
            elif key == "wmem_default":
                options["/net/core/wmem_default"] = value
            elif key == "window_scaling":
                if value == "on":
                    options["/net/ipv4/tcp_window_scaling"] = 1
                elif value == "off":
                    options["/net/ipv4/tcp_window_scaling"] = 0
                else:
                    print_wrong_usage(x)
                    return False
            elif key == "tcp_rmem_min":
                tcp_rmem["0"] = value
            elif key == "tcp_rmem_default":
                tcp_rmem["1"] = value
            elif key == "tcp_rmem_max":
                tcp_rmem["2"] = value
            elif key == "tcp_wmem_min":
                tcp_wmem["0"] = value
            elif key == "tcp_wmem_default":
                tcp_wmem["1"] = value
            elif key == "tcp_wmem_max":
                tcp_wmem["2"] = value
            else:
                print_wrong_usage(x)
                return False
    except IndexError:
        print_wrong_usage(x)
        return False
    # retrieve host information from conf
    dic["user"] = conf.get_user(dic["host_name"])
    dic["ip_control"] = conf.get_control_ip(dic["host_name"])
    # set options
    if not set_options(x, dic, options, tcp_rmem, tcp_wmem):
        return False
    return True
