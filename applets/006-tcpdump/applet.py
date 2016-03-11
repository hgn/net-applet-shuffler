
def main(x, conf, args):

    if not len(args) == 5:
        x.p.msg("wrong usage. use: host:[name] id:[number] mode:[start|stop] "
                "ofile=\"[filename]\" filter=\"[filter]\"\n")
        return False

    # arguments dictionary
    arg_d = {}
    arg_d["host_name"] = args[0].split(":")[1]
    arg_d["applet_id"] = args[1].split(":")[1]
    arg_d["applet_mode"] = args[2].split(":")[1]
    arg_d["output_file"] = args[3].split("\"")[1]
    arg_d["filter"] = args[4].split("\"")[1]

    # retrieve: host ip, host user name
    host_ip = conf['boxes'][arg_d["host_name"]]["interfaces"][0]['ip-address']
    host_interface = conf['boxes'][arg_d["host_name"]][0]['name']
    host_user = conf['boxes'][arg_d["host_name"]]['user']

    # applet mode:
    # start: start the tcpdumpp
    # stop: stop the tcpdump
    if arg_d["applet_mode"] == "start":

        stdout, stderr, exit_code = x.ssh.exec(host_ip, host_user,
                "mkdir /tmp/net-applet-shuffler")

        # connect to host and start tcpdump
        # https://wiki.ubuntuusers.de/tcpdump/
        # tcpdump -i [interface] [protocol] -n -s 0 -w
        # /tmp/net-applet-shuffler/[filename] '[filter(e.g. dst port 20000)]
        stdout, stderr, exit_code = x.ssh.exec(host_ip, host_user,
                "tcpdump -i {} -n -s 0 -w /tmp/net-applet-shuffler/{} '{"
                "}'".format(host_interface, arg_d["output_file"], arg_d["filter"]))

        if exit_code != 0:
            x.p.msg("error: tcpdump could not be started at host {}\n"
                    "failed params:\n".format(arg_d["host_name"]))
            x.p.msg("tcpdump -i {} -n -s 0 -w /tmp/net-applet-shuffler/{} '{}'".format(
                    host_interface, arg_d["output_file"], arg_d["filter"]))
            return False

        # retrieve tcpdump pid
        # there will be two processes running, tcpdump and the file writer
        # the dump will have a sudo in front and end the writer gracefully,
        # if ended gracefully
        pid_tcpdump = "0"
        stdout = x.ssh.exec(host_ip, host_user, "ps -ef | grep tcpdump")
        stdout_decoded = stdout[0].decode("utf-8")
        for x in stdout_decoded.splitlines():
            # unique identifier
            if "sudo tcpdump -i {} -n -s 0 -w /tmp/net-applet-shuffler/{} '{}'".format(
                    host_interface, arg_d["output_file"], arg_d["filter"]) in x:
                pid_tcpdump = x.split()[1]

        # save pid to file
        x.ssh.exec(host_ip, host_user, "touch "
                "/tmp/net-applet-shuffler/tcpdump_{}".format(arg_d["applet_id"]))
        x.ssh.exec(host_ip, host_user, "sh -c \"echo '{}' > /tmp/net-applet-shuffler/"
                "tcpdump_{}\"".format(pid_tcpdump, arg_d["applet_id"]))

        return True

    # applet mode:
    # start: start the tcpdumpp
    # stop: stop the tcpdump
    if arg_d["applet_mode"] == "stop":

        pid_tcpdump = "0"
        # retrieve pid
        stdout, stderr, exit_code = x.ssh.exec(host_ip, host_user, "echo "
                "\"$(</tmp/net-applet-shuffler/tcpdump_{})\"".format(arg_d["applet_id"]))
        pid_tcpdump = stdout.decode("utf-8").splitlines()[0]

        if exit_code != 0:
            x.p.msg("error: tcpdump pid at host {} could not be retrieved\n"
                    "failed params:\n".format(arg_d["host_name"]))
            x.p.msg("echo \"$(</tmp/net-applet-shuffler/tcpdump_{})\"".format(arg_d["applet_id"]))

            return False

        # end tcpdump gracefully
        x.ssh.exec(host_ip, host_user, "kill -2 {}".format(pid_tcpdump))
        x.ssh.exec(host_ip, host_user, "kill {}".format(pid_tcpdump))

        x.ssh.exec(host_ip, host_user, "rm /tmp/net-applet-shuffler/tcpdump_{"
                "}".format(arg_d["applet_id"]))

        return True
