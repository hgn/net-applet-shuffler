
import os


def main(x, conf, args):

    if not len(args) == 8:
        x.p.msg("wrong usage. use: [name] sink:[name] id:[id] source_port:["
                "port] sink_port:[port] length:[bytes|seconds] "
                "flow_offset:[seconds] netserver:[port]\n")
        return False

    # arguments dictionary
    arg_d = dict()
    arg_d["name_source"] = args[0]
    arg_d["name_dest"] = args[1].split(":")[1]
    arg_d["applet_id"] = args[2].split(":")[1]
    arg_d["port_source"] = args[3].split(":")[1]
    arg_d["port_dest"] = args[4].split(":")[1]
    arg_d["test_length"] = args[5].split(":")[1]
    arg_d["flow_offset"] = args[6].split(":")[1]
    arg_d["netserver_port"] = args[7].split(":")[1]
    # retrieve: source ip, source user name, destination ip, destination user name
    arg_d["ip_source"] = conf['boxes'][arg_d["name_source"]]["interfaces"][0]['ip-address']
    arg_d["user_source"] = conf['boxes'][arg_d["name_source"]]['user']
    arg_d["ip_dest"] = conf['boxes'][arg_d["name_dest"]]["interfaces"][0]['ip-address']
    arg_d["user_dest"] = conf['boxes'][arg_d["name_dest"]]['user']
    # assemble arguments
    arguments_string = "{} {} {} {} {} {} {} {} {} {} {} {}".format(
        arg_d["applet_id"], arg_d["name_source"], arg_d["user_source"],
        arg_d["ip_source"], arg_d["port_source"], arg_d["name_dest"],
        arg_d["user_dest"], arg_d["ip_dest"], arg_d["port_dest"],
        arg_d["netserver_port"], arg_d["test_length"], arg_d["flow_offset"])
    # netperf controller path
    local_net_path = os.path.dirname(os.path.realpath(__file__)) + \
                     ("/netperf-controller.py")
    remote_net_path = "/tmp/net-applet-shuffler/netperf-controller.py"
    # check if netperf controller is already on source
    _, _, exit_code = x.ssh.exec(arg_d["ip_source"], arg_d["user_source"],
                                 "test -f {}".format(remote_net_path))
    if not exit_code == 0:
        # netperf controller does not exist on host
        # due to permission restrictions, scp can't copy to tmp directly
        # 1. temp copy to user home
        x.ssh.copy(arg_d["user_source"], arg_d["ip_source"], "/home/{}/tmp_f"
                   .format(arg_d["user_source"]), local_net_path, False)
        # 2. make target dir
        x.ssh.exec(arg_d["ip_source"], arg_d["user_source"],
                   "mkdir /tmp/net-applet-shuffler")
        # 3. copy to target location
        x.ssh.exec(arg_d["ip_source"], arg_d["user_source"],
                   "cp /home/{}/tmp_f {}".format(arg_d["user_source"],
                                                 remote_net_path))
        # 4. remove temp copy
        x.ssh.exec(arg_d["ip_source"], arg_d["user_source"],
                   "rm -f /home/{}/tmp_f".format(arg_d["user_source"]))
    # run netperf controller at source in background
    x.p.msg("python3.5 {} {} &".format(remote_net_path, arguments_string))
    x.ssh.exec(arg_d["ip_source"], arg_d["user_source"], "python3.5 {} {} &"
               .format(remote_net_path, arguments_string))

    return True
