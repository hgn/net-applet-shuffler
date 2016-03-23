
import os
import subprocess


def tcpdump_start(x, arg_d):
    x.ssh.exec(arg_d["host_ip"], arg_d["host_user"],
            "mkdir /tmp/net-applet-shuffler")
    # connect to host and start tcpdump
    # https://wiki.ubuntuusers.de/tcpdump/
    # tcpdump -i [interface] [protocol] -n -s 0 -w
    # /tmp/net-applet-shuffler/[filename] '[filter(e.g. dst port 20000)]
    _, _, exit_code = x.ssh.exec(arg_d["host_ip"], arg_d["host_user"],
            "tcpdump -i {} -n -s 0 -w /tmp/net-applet-shuffler/dump_{}.pcap "
            "'{}' &".format(arg_d["host_interface"], arg_d["applet_id"],
                          arg_d["filter"]))

    if exit_code != 0:
        x.p.msg("error: tcpdump could not be started at host {}\n"
                "failed params:\n".format(arg_d["host_name"]))
        x.p.msg("tcpdump -i {} -n -s 0 -w "
                "/tmp/net-applet-shuffler/dump_{}.pcap '{}'".format
                (arg_d["host_interface"], arg_d["applet_id"], arg_d["filter"]))
        return False

    # retrieve tcpdump pid
    # there will be two processes running, tcpdump and the file writer
    # the dump will have a sudo in front and end the writer gracefully,
    # if ended gracefully
    pid_tcpdump = "0"
    stdout = x.ssh.exec(arg_d["host_ip"], arg_d["host_user"],
                        "ps -ef | grep tcpdump")
    stdout_decoded = stdout[0].decode("utf-8")
    for line in stdout_decoded.splitlines():
        # unique identifier
        if "sudo tcpdump -i {} -n -s 0 -w /tmp/net-applet-shuffler/tcpdump_{} " \
           "'{}'".format(arg_d["host_interface"], arg_d["applet_id"],
                         arg_d["filter"]) in line:
            pid_tcpdump = line.split()[1]

    # save pid to file
    path_to_tcpdump_pid = "/tmp/net-applet-shuffler/tcpdump_{" \
                          "}".format(arg_d["applet_id"])
    x.ssh.exec(arg_d["host_ip"], arg_d["host_user"], "touch {"
            "}".format(path_to_tcpdump_pid))
    x.ssh.exec(arg_d["host_ip"], arg_d["host_user"], "sh -c \"echo '{}' > "
            "{}\"".format(pid_tcpdump, path_to_tcpdump_pid))

    return True


def transfer_dumpfile(x, arg_d):

    # make local directories
    try:
        os.makedirs(arg_d["local_file_name"])
    except os.error:
        # path/file exsits
        pass
    # use secure copy to retrieve the dump file
    process = subprocess.Popen("scp {}@{}:/tmp/net-applet-shuffler/dump_{}.pcap"
            " {}".format(arg_d["host_user"], arg_d["host_ip"],
            arg_d["applet_id"], arg_d["local_file_name"]).split(),
            stdout=subprocess.PIPE)
    # block until file transfer is done
    process.communicate()
    if process.returncode != 0:
        x.p.msg("error transferring the dumpfile dump_{}.pcap from host {"
                "}".format(arg_d["applet_id"], arg_d["host_name"]))
        return False

    # clean up dumpfile on host
    x.ssh.exec(arg_d["host_ip"], arg_d["host_user"], "rm "
            "/tmp/net-applet-shuffler/dump_{}.pcap".format(arg_d["applet_id"]))

    return True


def tcpdump_stop(x, arg_d):
    # retrieve pid
    stdout, _, exit_code = x.ssh.exec(arg_d["host_ip"], arg_d["host_user"],
            "echo \"$(</tmp/net-applet-shuffler/tcpdump_{})\""
            .format(arg_d["applet_id"]))

    if exit_code != 0:
        x.p.msg("error: tcpdump pid at host {} could not be retrieved\n"
                "failed params:\n".format(arg_d["host_name"]))
        x.p.msg("echo \"$(</tmp/net-applet-shuffler/tcpdump_{})\""
                .format(arg_d["applet_id"]))
        return False

    pid_tcpdump = stdout.decode("utf-8").splitlines()[0]
    # end tcpdump gracefully
    x.ssh.exec(arg_d["host_ip"], arg_d["host_user"],
               "kill -2 {}".format(pid_tcpdump))
    x.ssh.exec(arg_d["host_ip"], arg_d["host_user"],
               "kill {}".format(pid_tcpdump))
    x.ssh.exec(arg_d["host_ip"], arg_d["host_user"],
               "rm /tmp/net-applet-shuffler/tcpdump_{"
               "}".format(arg_d["applet_id"]))

    x.p.msg("fetching dumpfile from {}".format(arg_d["host_name"]))
    if not transfer_dumpfile(x, arg_d):
        return False

    return True


def main(x, conf, args):
    if not len(args) >= 4:
        x.p.msg("wrong usage. use: [hostname] id:[number] mode:[start|stop] "
                "local-file-name:\"[filename]\" filter:\"[filter]\"\n")
        return False

    # arguments dictionary
    arg_d = dict()
    arg_d["host_name"] = args[0]
    arg_d["applet_id"] = args[1].split(":")[1]
    arg_d["applet_mode"] = args[2].split(":")[1]
    arg_d["local_file_name"] = args[3].split("\"")[1]
    arg_d["filter"] = args[4].split("\"")[1]
    # retrieve: host ip, host user name
    arg_d["host_ip"] = conf['boxes'][arg_d["host_name"]]["interfaces"][0]['ip-address']
    arg_d["host_interface"] = conf['boxes'][arg_d["host_name"]]['interfaces'][0]['name']
    arg_d["host_user"] = conf['boxes'][arg_d["host_name"]]['user']

    # applet mode:
    # start: start the tcpdump
    # black voodoo magic: arg_d["applet_mode"] is "start" does not work
    if arg_d["applet_mode"] == "start":
        x.p.msg("starting tcpdump at host {}".format(arg_d["host_name"]))
        if tcpdump_start(x, arg_d):
            return True
        return False

    # applet mode:
    # stop: stop the tcpdump
    # blocks until file is transferred
    if arg_d["applet_mode"] == "stop":
        x.p.msg("stopping tcpdump at host {}".format(arg_d["host_name"]))
        if tcpdump_stop(x, arg_d):
            return True
        return False
