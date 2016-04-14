# usage: exec [host] control:"[full|partial]"
#  exec [host] control:full netem:"[command]"
#  exec [host] control:partial change:[add|del|change|replace] to-network:[name]
#   command:"[command]"
# Check success:
#  - tc -s qdisc ls dev [interface]
# Examples:
#  - tc qdisc change dev enp3s2 root netem delay 200ms

from time import strftime


def print_usage(x):
    x.p.msg("\n usage:\n", False)
    x.p.msg(" - exec 104-netem-cmd [host] control:\"[full|partial]\"\n", False)
    x.p.msg(" - [host] control:full netem:\"[command]\"\n", False)
    x.p.msg(" - [host] control:partial change:[add|del|change|replace] "
            "to-network:[name] command:\"[command]\"\n", False)
    x.p.msg("\n check success:\n", False)
    x.p.msg(" - tc -s qdisc ls dev [interface]\n", False)
    return False


def qdisc_log(x, dic, cmd):
    time_now = strftime("%H:%M:%S")
    time_cmd = time_now + " \t" + cmd
    # make sure directories and logfile exist
    x.ssh.exec(dic["ip_control"], dic["user"], "mkdir -p "
                                               "/tmp/net-applet-shuffler")
    x.ssh.exec(dic["ip_control"], dic["user"],
               "mkdir -p /tmp/net-applet-shuffler/logs")
    x.ssh.exec(dic["ip_control"], dic["user"],
               "touch /tmp/net-applet-shuffler/logs/qdisc_log")
    x.ssh.exec(dic["ip_control"], dic["user"], "sh -c \"echo '{}' >> "
               "/tmp/net-applet-shuffler/logs/qdisc_log\"".format(time_cmd))
    return True


def set_netem_full(x, dic):
    _, _, exit_code = x.ssh.exec(dic["ip_control"], dic["user"],
                                 dic["netem_cmd"])
    if exit_code != 0:
        qdisc_log(x, dic, "FAILED sudo " + dic["netem_cmd"])
        x.p.err("error: netem could not be set\n")
        x.p.err("failed cmd: \"{}\"\n".format(dic["netem_cmd"]))
        return False

    qdisc_log(x, dic, "sudo " + dic["netem_cmd"])
    return True


def set_netem_part(x, dic):
    cmd = str()
    if dic["change"] == "del":
        cmd = "tc qdisc del dev {} root netem".format(dic["device"])
    else:
        cmd = "tc qdisc {} dev {} root netem {}".format(dic["change"],
                                                        dic["device"],
                                                        dic["netem_cmd"])
    _, _, exit_code = x.ssh.exec(dic["ip_control"], dic["user"], cmd)
    if exit_code != 0:
        qdisc_log(x, dic, "FAILED sudo " + cmd)
        x.p.err("error: netem could not be set\n")
        x.p.err("failed cmd: \"{}\"\n".format(cmd))
        return False

    qdisc_log(x, dic, "sudo " + cmd)
    return True


def netem_full_handler(x, conf, args, dic):
    try:
        dic["host_name"] = args[0]
        position = 2
        netem_cmd = args[position].split(":")[1]
        # this part is for argument handling when called from exec-campaign
        try:
            while True:
                position += 1
                netem_cmd += " " + args[position]
        except IndexError:
            pass
        # cut beginning and trailing "
        dic["netem_cmd"] = netem_cmd.strip("\"")
    except IndexError:
        x.p.err("error: wrong usage\n")
        return False
    dic["user"] = conf.get_user(dic["host_name"])
    dic["ip_control"] = conf.get_control_ip(dic["host_name"])
    # set netem
    if not set_netem_full(x, dic):
        return False
    return True


def netem_part_handler(x, conf, args, dic):
    try:
        dic["host_name"] = args[0]
        dic["change"] = args[2].split(":")[1]
        to_network = args[3].split(":")[1]
        dic["device"] = conf.get_middle_box_iface_name_by_network_name\
            (dic["host_name"], to_network)
        if dic["change"] != "del":
            # command
            position = 4
            netem_cmd = args[position].split(":")[1]
            # this part is for argument handling when called from exec-campaign
            try:
                while True:
                    position += 1
                    netem_cmd += " " + args[position]
            except IndexError:
                pass
            dic["netem_cmd"] = netem_cmd.strip("\"")
    except IndexError:
        x.p.err("error: wrong usage\n")
        return False
    dic["user"] = conf.get_user(dic["host_name"])
    dic["ip_control"] = conf.get_control_ip(dic["host_name"])
    # set netem
    if not set_netem_part(x, dic):
        return False
    return True


def main(x, conf, args):
    if "?" in args:
        return print_usage(x)
    if not len(args) >= 3:
        x.p.err("error: wrong usage\n")
        return False
    # arguments dictionary
    dic = dict()
    dic["control"] = args[1].split(":")[1]

    # full control
    if dic["control"] == "full":
        return netem_full_handler(x, conf, args, dic)
    # partial control
    elif dic["control"] == "partial":
        return netem_part_handler(x, conf, args, dic)
    else:
        x.p.err("error: wrong usage\n")
        return False
