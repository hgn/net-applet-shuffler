
import os
import time

from threading import Thread


def tcpdump_start_thread(x, arg_d):
    # connect to host and start tcpdump
    # https://wiki.ubuntuusers.de/tcpdump/
    # tcpdump -i [interface] [protocol] -n -s 0 -w
    # /tmp/net-applet-shuffler/[filename] '[filter(e.g. dst port 20000)]
    x.ssh.exec(arg_d["host_ip_control"], arg_d["host_user"], "tcpdump -i {} -n"
               " -s 0 -w /tmp/net-applet-shuffler/tcpdump_{}.pcap '{}'"
               .format(arg_d["host_interface"], arg_d["applet_id"],
                       arg_d["filter_or_file"]))


def tcpdump_start(x, arg_d):
    x.ssh.exec(arg_d["host_ip_control"], arg_d["host_user"],
               "mkdir -p /tmp/net-applet-shuffler")
    tcp_thread = Thread(target=tcpdump_start_thread, args=(x, arg_d, ))
    tcp_thread.daemon = True
    tcp_thread.start()
    # retrieve tcpdump pid
    # there will be two processes running, tcpdump and the file writer
    # the dump will have a sudo in front and end the writer gracefully,
    # if ended gracefully
    pid_tcpdump = "0"
    no_pid_found = True
    tcp_pid_fetch_tries = 5
    while tcp_pid_fetch_tries > 0 and no_pid_found:
        stdout, _, _ = x.ssh.exec_verbose(arg_d["host_ip_control"],
                                          arg_d["host_user"],
                                          "ps -ef | grep tcpdump")
        stdout_decoded = stdout.decode("utf-8")
        for line in stdout_decoded.splitlines():
            # unique identifier
            if "sudo tcpdump -i {} -n -s 0 -w /tmp/net-applet-shuffler/" \
                    "tcpdump_{}.pcap '{}'".format(arg_d["host_interface"],
                    arg_d["applet_id"], arg_d["filter_or_file"]) in line:
                pid_tcpdump = line.split()[1]
                no_pid_found = False
        tcp_pid_fetch_tries -= 1
        time.sleep(1)

    if no_pid_found:
        x.p.err("error: tcpdump pid on host {} could not be "
                "retrieved\n".format(arg_d["host_name"]))
        return False

    # save pid to file
    path_to_tcpdump_pid = "/tmp/net-applet-shuffler/tcpdump_{}"\
                          .format(arg_d["applet_id"])
    exit_code_1 = x.ssh.exec(arg_d["host_ip_control"], arg_d["host_user"],
                             "touch {}".format(path_to_tcpdump_pid))
    exit_code_2 = x.ssh.exec(arg_d["host_ip_control"], arg_d["host_user"],
                             "sh -c \"echo '{}' > {}\""
                             .format(pid_tcpdump, path_to_tcpdump_pid))
    if (exit_code_1 or exit_code_2) != 0:
        x.p.msg("problem (no abort): tcpdump pid could not be saved to file on"
                " host {}\n".format(arg_d["name_host"]))

    return True


def dumpfile_is_empty(x, arg_d):
    file_statistics = os.stat(os.path.join(arg_d["file_path"],
                                           arg_d["file_name"]))
    if file_statistics.st_size == 0:
        x.p.err("error: dumpfile {}/{} has size 0\n"
                .format(arg_d["file_path"], arg_d["file_name"]))
        return True

    return False


def create_file_path(x, arg_d):
    # relative file path logic
    file_path = str()
    file_name = str()
    # note: the current file path is two levels below nas
    # path and file name shuffling magic
    if arg_d["path_usage"] == "relative":
        current_file_dir = os.path.dirname(__file__)
        # nas file path + dir and filename to dst file
        file_path_full = os.path.join(current_file_dir + "/../../",
                                 arg_d["filter_or_file"])
        # make local directories
        file_path_split = file_path_full.split("/")
        file_name = file_path_split[len(file_path_split)-1]
        file_path_split.pop(len(file_path_split)-1)
        file_path = "/".join(file_path_split)
    # absolute file path logic
    elif arg_d["path_usage"] == "absolute":
        # make local directories
        file_path_split = arg_d["filter_or_file"].split("/")
        file_name = file_path_split[len(file_path_split)-1]
        try:
            file_path_split.pop(len(file_path_split)-1)
            file_path = "/".join(file_path_split)
        except IndexError:
            # this means the top directory is used
            # will throw a permission denied anyways
            file_path = "/"

    if not (file_path or file_name):
        x.p.err("error: file path and/or name is/are empty\n")
        return False
    arg_d["file_path"] = file_path
    arg_d["file_name"] = file_name

    return True


def transfer_dumpfile(x, arg_d):
    # create file path
    if not create_file_path(x, arg_d):
        x.p.err("error: file path could not be created\n")
        return False
    # tcpdump process run autonomously and it seems it might take some time,
    # before the dumpfile is filled with data
    # thus, the perfect solution would be a join with the tcpdump thread
    # here: poor mans solution
    time.sleep(2)
    # retrieve dump file and block until it's done
    _, _, exit_code = x.ssh.copy_from(arg_d["host_user"],
                                      arg_d["host_ip_control"],
                                      "/tmp/net-applet-shuffler",
                                      arg_d["file_path"], "tcpdump_{}.pcap"
                                      .format(arg_d["applet_id"]),
                                      arg_d["file_name"])
    if exit_code != 0:
        x.p.err("error: transferring the dumpfile tcpdump_{}.pcap from host "
                "{}\n".format(arg_d["applet_id"], arg_d["host_name"]))
        return False
    # clean up dumpfile on host
    x.ssh.exec(arg_d["host_ip_control"], arg_d["host_user"],
               "rm /tmp/net-applet-shuffler/tcpdump_{}.pcap"
               .format(arg_d["applet_id"]))
    # Check if the dumpfile is empty -> error
    if dumpfile_is_empty(x, arg_d):
        x.p.err("error: tcpdump file is empty, either the filter is bad or "
                "something went wrong\n")
        return False

    return True


def tcpdump_stop(x, arg_d):
    # retrieve pid
    stdout, _, exit_code = x.ssh.exec_verbose(arg_d["host_ip_control"],
            arg_d["host_user"], "echo \"$(</tmp/net-applet-shuffler/tcpdump_{}"
                                ")\"".format(arg_d["applet_id"]))

    if exit_code != 0:
        x.p.err("error: tcpdump pid at host {} could not be retrieved\n"
                "failed params: ".format(arg_d["host_name"]))
        x.p.err("echo \"$(</tmp/net-applet-shuffler/tcpdump_{})\"\n"
                .format(arg_d["applet_id"]))
        return False

    pid_tcpdump = stdout.decode("utf-8").splitlines()[0]
    # end tcpdump gracefully
    x.ssh.exec(arg_d["host_ip_control"], arg_d["host_user"],
               "kill -2 {}".format(pid_tcpdump))
    x.ssh.exec(arg_d["host_ip_control"], arg_d["host_user"],
               "kill {}".format(pid_tcpdump))
    x.ssh.exec(arg_d["host_ip_control"], arg_d["host_user"],
               "rm /tmp/net-applet-shuffler/tcpdump_{"
               "}".format(arg_d["applet_id"]))

    x.p.msg("fetching dumpfile from {}\n".format(arg_d["host_name"]))
    if not transfer_dumpfile(x, arg_d):
        return False

    return True


def main(x, conf, args):
    if not len(args) >= 4:
        x.p.err("wrong usage. use: [hostname] id:[number] mode:[start|stop]\n"
                "mode:start -> \tfilter:\"[filter]\"\n"
                "mode:stop -> \tlocal-file-name:[filename]\"\n")
        return False
    # arguments dictionary
    arg_d = dict()
    try:
        arg_d["host_name"] = args[0]
        arg_d["applet_id"] = args[1].split(":")[1]
        arg_d["applet_mode"] = args[2].split(":")[1]
        path_usage = args[3].split(":")[1].strip("\"")
        if arg_d["applet_mode"] == "stop":
            if path_usage[0] == "/":
                arg_d["path_usage"] = "absolute"
            else:
                arg_d["path_usage"] = "relative"
        # string handling:
        # the shell cuts " or ' when arguments are used
        # tcpdumps filter via exec-applet can look like:
        # 'filter:tcp and dst port 20000'
        # tcpdumps filter via exec-campaign:
        # 'filter:"tcp', 'and', 'dst', 'port', '30000"'
        filter_or_file_str = args[3].split(":")[1]
        position = 3
        # this part is for argument handling when called from exec-campaign
        try:
            while True:
                position += 1
                filter_or_file_str += " " + args[position]
        except IndexError:
            pass
        # cut beginning and trailing "
        arg_d["filter_or_file"] = filter_or_file_str.strip("\"")
    except IndexError:
        x.p.err("error: wrong usage\n")
        return False
    # retrieve: host ip, host user name
    arg_d["host_ip_control"] = conf.get_control_ip(arg_d["host_name"])
    arg_d["host_interface"] = conf.get_data_iface_name(arg_d["host_name"])
    arg_d["host_user"] = conf.get_user(arg_d["host_name"])
    # applet mode:
    # start: start the tcpdump
    # black voodoo magic: arg_d["applet_mode"] is "start" does not work
    if arg_d["applet_mode"] == "start":
        x.p.msg("starting tcpdump at host {}\n".format(arg_d["host_name"]))
        if tcpdump_start(x, arg_d):
            return True
        return False
    # applet mode:
    # stop: stop the tcpdump
    # blocks until file is transferred
    elif arg_d["applet_mode"] == "stop":
        x.p.msg("stopping tcpdump at host {}\n".format(arg_d["host_name"]))
        if tcpdump_stop(x, arg_d):
            return True
        return False
    else:
        x.p.err("error: wrong applet mode")
        return False
