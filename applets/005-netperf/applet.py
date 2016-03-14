
def netserver_end(x, arg_d):
    # try graceful end
    x.ssh.exec(arg_d["ip_dest"], arg_d["user_dest"], "kill -2 {"
            "}".format(arg_d["netserver_pid"]))
    # resort to kill
    x.ssh.exec(arg_d["ip_dest"], arg_d["user_dest"], "kill {"
            "}".format(arg_d["netserver_pid"]))
    # remove pid file
    x.ssh.exec(arg_d["ip_dest"], arg_d["user_dest"], "rm "
            "/tmp/net-applet-shuffler/netserver_{}".format(arg_d["applet_id"],
                                                    arg_d["netserver_pid"]))

    return True


def netserver_start(x, arg_d):
    # pid of netserver which is about to be started
    netserver_pid = "0"
    # netperf needs a netserver at target listening on a specific port (
    # control port)
    _, _, exit_code = x.ssh.exec(arg_d["ip_dest"], arg_d["user_dest"],
            "netserver -4 -p {}".format(arg_d["netserver_port"]))
    # in case of error, there is a netserver possibly already running
    if exit_code != 0:
        x.p.msg("error: netserver (required for netperf) could not be started "
                "at {}\n".format(arg_d["name_dest"]))
        return False, netserver_pid

    # get the process id of the just started netserver != pid of ssh.exec
    # process
    # Note: "pgrep netserver" does not work, since we want to get a specific one
    stdout = x.ssh.exec(arg_d["ip_dest"], arg_d["user_dest"],
                        "ps -ef | grep netserver")
    stdout_decoded = stdout[0].decode("utf-8")
    for x in stdout_decoded.splitlines():
        # unique identifier
        if "netserver -4 -p {}".format(arg_d["netserver_port"]) in x:
            netserver_pid = x.split()[1]

    return True, netserver_pid


def test_running(x, arg_d, starting):
    # while the following file exists, there is a ongoing transfer
    if starting:
        x.ssh.exec(arg_d["ip_dest"], arg_d["user_dest"], "touch "
                "/tmp/net-applet-shuffler/running_{}".format(arg_d["applet_id"]))
    if not starting:
        x.ssh.exec(arg_d["ip_dest"], arg_d["user_dest"], "rm "
                "/tmp/net-applet-shuffler/running_{}".format(arg_d["applet_id"]))

    return True


def main(x, conf, args):

    if not len(args) == 8:
        x.p.msg("wrong usage. use: [name] sink:[name] id:[id] source_port:["
                "port] sink_port:[port] length:[bytes|seconds] "
                "transfer_offset:[seconds] netserver:[port]\n")
        return False

    # arguments dictionary
    arg_d = {}
    arg_d["name_source"] = args[0]
    arg_d["name_dest"] = args[1].split(":")[1]
    arg_d["applet_id"] = args[2].split(":")[1]
    arg_d["port_source"] = args[3].split(":")[1]
    arg_d["port_dest"] = args[4].split(":")[1]
    arg_d["test_length"] = args[5].split(":")[1]
    arg_d["transfer_offset"] = args[6].split(":")[1]
    arg_d["netserver_port"] = args[7].split(":")[1]
    x.p.msg("netperf: starting source {}:{} with sink {}:{}, "
            "length {} and offset {}. Netserver: {}:{}\n".format(
            arg_d["name_source"], arg_d["port_source"], arg_d["name_dest"],
            arg_d["port_dest"], arg_d["test_length"], arg_d["transfer_offset"],
            arg_d["name_dest"], arg_d["netserver_port"]))
    # retrieve: source ip, source user name, destination ip, destination user name
    arg_d["ip_source"] = conf['boxes'][arg_d["name_source"]]["interfaces"][0]['ip-address']
    arg_d["user_source"] = conf['boxes'][arg_d["name_source"]]['user']
    arg_d["ip_dest"] = conf['boxes'][arg_d["name_dest"]]["interfaces"][0]['ip-address']
    arg_d["user_dest"] = conf['boxes'][arg_d["name_dest"]]['user']

    # start netserver on destination
    netserver_started, arg_d["netserver_pid"] = netserver_start(x, arg_d)
    # return false if netserver could not be started
    if not netserver_started:
        return False
    # save netserver pid to /tmp/net-applet-shuffler/netserver_[pid]
    # if start succeeded
    x.ssh.exec(arg_d["ip_dest"], arg_d["user_dest"], "mkdir "
                                                    "/tmp/net-applet-shuffler")
    x.ssh.exec(arg_d["ip_dest"], arg_d["user_dest"], "touch "
            "/tmp/net-applet-shuffler/netserver_{}".format(arg_d["applet_id"]))
    x.ssh.exec(arg_d["ip_dest"], arg_d["user_dest"], "sh -c \"echo '{}' > "
            "/tmp/net-applet-shuffler/netserver_{}\"".format(
            arg_d["netserver_pid"], arg_d["applet_id"]))
    # write test in progress file
    # to be checked if there are ongoing transfers
    test_running(x, arg_d, True)
    # begin test, as a non-blocking background process
    # here, traffic flows from source to destination
    # netperf -H [dest_ip],[ipv4] -L [source_ip],[ipv4] -p [
    # netserver_control_port] -l [flow_length: bytes(<0) or seconds(>0)] -s [
    # seconds_to_wait_before_test] -- -P [port_source],[port_target] -T [
    # protocol] -4
    _, _, exit_code = x.ssh.exec(arg_d["ip_source"], arg_d["user_source"],
            "netperf -H {},4 -L {},4 -p {} -l {} -s {} -- -P {},{} -T TCP "
            "-4 &".format(arg_d["ip_dest"], arg_d["ip_source"],
            arg_d["netserver_port"], arg_d["test_length"],
            arg_d["transfer_offset"], arg_d["port_source"], arg_d["port_dest"]))

    if exit_code != 0:
        x.p.msg("error: netperf performance test could not be "
                "executed\nfailed params:\n")
        x.p.msg("netperf -H {},4 -L {},4 -p {} -l {} -s {} -- -P {},{} -T TCP "
            "-4\n".format(arg_d["ip_dest"], arg_d["ip_source"],
            arg_d["netserver_port"], arg_d["test_length"],
            arg_d["transfer_offset"], arg_d["port_source"], arg_d["port_target"]))
        return False
    test_running(x, arg_d, False)

    netserver_end(x, arg_d)

    return True
