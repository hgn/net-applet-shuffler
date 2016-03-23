
import os
import subprocess

from threading import Thread

LOCAL_NET_PATH = os.path.dirname(os.path.realpath(__file__))
REMOTE_NET_PATH = "/tmp/net-applet-shuffler"


def ssh_exec(ip, user, cmd):
    ssh_command = "ssh {}@{} sudo {}".format(user, ip, cmd)
    process = subprocess.Popen(ssh_command.split(), stdout=subprocess.PIPE)
    stdout, stderr = process.communicate()
    return stdout, stderr, process.returncode


def scp(remote_user, remote_ip, remote_path, local_path, to_local):
    command = str()
    if to_local:
        command = "scp {}@{}:{} {}".format(remote_user, remote_ip, remote_path,
                                           local_path)
    else:
        command = "scp {} {}@{}:{}".format(local_path, remote_user, remote_ip,
                                           remote_path)
    p = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    stdout, stderr = p.communicate()
    return stdout, stderr, p.returncode


def controller_thread(arg_d):
    # assemble arguments
    arguments_string = "{} {} {} {} {} {} {} {} {} {} {} {}".format(
        arg_d["applet_id"], arg_d["name_source"], arg_d["user_source"],
        arg_d["ip_source"], arg_d["port_source"], arg_d["name_dest"],
        arg_d["user_dest"], arg_d["ip_dest"], arg_d["port_dest"],
        arg_d["netserver_port"], arg_d["flow_length"], arg_d["flow_offset"])
    # check if netperf controller is already on source
    _, _, exit_code = ssh_exec(arg_d["ip_source"], arg_d["user_source"],
                                 "test -f {}".format(REMOTE_NET_PATH))
    # if not, copy it to source
    if not exit_code == 0:
        copy_to_destination(arg_d["user_source"], arg_d["ip_source"],
                            LOCAL_NET_PATH, REMOTE_NET_PATH,
                            "netperf-controller.py", "netperf-controller.py")
    ssh_exec(arg_d["ip_source"], arg_d["user_source"], "python3.5 {}/{} {}"
               .format(REMOTE_NET_PATH, "netperf-controller.py",
                       arguments_string))


def copy_to_destination(user, ip, from_path, to_path, source_filename, dest_filename):
    # due to permission restrictions, scp can't copy to not user owned
    # places directly
    # 1. temp copy to user home
    scp(user, ip, "/home/{}/tmp_f".format(user),
               (from_path + "/" + source_filename), False)
    # 2. make target dir
    ssh_exec(ip, user, "mkdir {}".format(to_path))
    # 3. copy to target location
    ssh_exec(ip, user, "cp /home/{}/tmp_f {}/{}".format(user, to_path,
                                                            dest_filename))
    # 4. remove temp copy
    ssh_exec(ip, user, "rm -f /home/{}/tmp_f".format(user))


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
    arg_d["flow_length"] = args[5].split(":")[1]
    arg_d["flow_offset"] = args[6].split(":")[1]
    arg_d["netserver_port"] = args[7].split(":")[1]
    # retrieve: source ip, source user name, destination ip, destination user name
    arg_d["ip_source"] = conf['boxes'][arg_d["name_source"]]["interfaces"][0]['ip-address']
    arg_d["user_source"] = conf['boxes'][arg_d["name_source"]]['user']
    arg_d["ip_dest"] = conf['boxes'][arg_d["name_dest"]]["interfaces"][0]['ip-address']
    arg_d["user_dest"] = conf['boxes'][arg_d["name_dest"]]['user']
    # potentially start parallel netperf instances
    # note: at this point, the distribution of the applet will be done, which
    # is probably not the best way to do (can cause unwanted time offsets)
    contr_thread = Thread(target=controller_thread, args=(arg_d, ))
    contr_thread.start()

    return True
