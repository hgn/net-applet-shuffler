
def netserver_start(x, host_name, host_ip, host_user, netserver_port):


    # pid of netserver which is about to be started
    netserver_pid = "0"
    # netperf needs a netserver at target listening on a specific port (
    # control port)
    stdout, stderr, exit_code = x.ssh.exec(host_ip, host_user,
            "netserver -4 -p {}".format(netserver_port))
    # in case of error, there is a netserver possibly already running
    if exit_code != 0:
        x.p.msg("error: netserver (required for netperf) could not be started "
                "at {}\n".format(host_name))
        return False, netserver_pid

    # get the process id of the just started netserver != pid of ssh.exec
    # process
    # Note: "pgrep netserver" does not work, since we want to get a specific one
    stdout = x.ssh.exec(host_ip, host_user, "ps -ef | grep netserver")
    stdout_decoded = stdout[0].decode("utf-8")
    for x in stdout_decoded.splitlines():
        # unique identifier
        if "netserver -4 -p {}".format(netserver_port) in x:
            netserver_pid = x.split()[1]

    return True, netserver_pid


def main(x, conf, args):

    if not len(args) == 7:
        x.p.msg("wrong usage. use: source dest id:[id] sport:[port] "
                "dport:[port] length:[bytes|seconds] netserver:[port]\n")
        return False

    # arguments dictionary
    arg_d = {}
    arg_d["name_source"] = args[0]
    arg_d["name_dest"] = args[1]
    arg_d["applet_id"] = args[2].split(":")[1]
    arg_d["port_source"] = args[3].split(":")[1]
    arg_d["port_dest"] = args[4].split(":")[1]
    arg_d["test_length"] = args[5].split(":")[1]
    arg_d["netserver_port"] = args[6].split(":")[1]
    x.p.msg("netperf: starting host {}:{} with target {}:{} and "
            "length {}. Netserver: {}:{}\n".format(
            arg_d["name_source"], arg_d["port_source"], arg_d["name_dest"],
            arg_d["port_dest"], arg_d["test_length"],arg_d["name_dest"],
            arg_d["netserver_port"]))

    # retrieve: host ip, host user name, destination ip, destination user name
    ip_source = conf['boxes'][arg_d["name_source"]]["interfaces"][0]['ip-address']
    user_source = conf['boxes'][arg_d["name_source"]]['user']
    ip_dest = conf['boxes'][arg_d["name_dest"]]["interfaces"][0]['ip-address']
    user_dest = conf['boxes'][arg_d["name_dest"]]['user']

    # start netserver on destination
    netserver_started, netserver_pid = netserver_start(x, arg_d["name_dest"],
            ip_dest, user_dest, arg_d["netserver_port"])
    # return false if netserver could not be started
    if not netserver_started:
        return False
    # save netserver pid to /tmp/netserver_[hostname]_[pid] if start succeeded
    x.ssh.exec(ip_dest, user_dest, "touch /tmp/net-applet-shuffler/netserver_{"
            "}".format(arg_d["applet_id"]))
    x.ssh.exec(ip_dest, user_dest, "sh -c \"echo '{}' > /tmp/net-applet-shuffler/"
            "netserver_{}\"".format(netserver_pid, arg_d["applet_id"]))

    # begin test
    # here, traffic flows from source to destination
    # netperf -H [dest_ip],[ipv4] -L [source_ip],[ipv4] -p [
    # netserver_control_port] -l [flow_length: bytes(<0) or seconds(>0)] -s [
    # seconds_to_wait_before_test] -- -P [port_source],[port_target] -T [
    # protocol] -4
    stdout, stderr, exit_code = x.ssh.exec(ip_source, user_source,
            "netperf -H {},4 -L {},4 -p {} -l {} -s 1 -- -P {},{} -T TCP "
            "-4".format(ip_dest, ip_source, arg_d["netserver_port"],
            arg_d["test_length"], arg_d["port_source"], arg_d["port_dest"]))

    if exit_code != 0:
        x.p.msg("error: netperf performance test could not be "
                "executed\nfailed params:\n")
        x.p.msg("netperf -H {},4 -L {},4 -p {} -l {} -s 1 -- -P {},{} -T TCP "
            "-4\n".format(ip_dest, ip_source, arg_d["netserver_port"],
            arg_d["test_length"], arg_d["port_source"], arg_d["port_target"]))
        return False

    # end netserver
    # try graceful end
    x.ssh.exec(ip_dest, user_dest, "kill -2 {}".format(netserver_pid))
    # resort to kill
    x.ssh.exec(ip_dest, user_dest, "kill {}".format(netserver_pid))
    x.ssh.exec(ip_dest, user_dest, "rm /tmp/net-applet-shuffler/netserver_{"
            "}".format(arg_d["applet_id"], netserver_pid))

    return True
