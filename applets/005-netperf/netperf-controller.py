
import os
import sys
import subprocess


class NetperfController:

    def demonize_program(self):
        # https://gist.github.com/andreif/cbb71b0498589dac93cb
        # first fork
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(1)
        except OSError as error:
            sys.stderr.write("first process forking failed:\n{}\n".format(
                                                                        error))
            sys.exit(1)
        # decoupling
        os.chdir("/")
        os.setsid()
        os.umask(0)
        # second fork
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError as error:
            sys.stderr.write("second process forking failed:\n{}\n".format(
                                                                        error))
            sys.exit(1)
        # redirection of standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        std_in = open(os.devnull, "r")
        std_out = open(os.devnull, "a+")
        std_err = open(os.devnull, "a+")
        os.dup2(std_in.fileno(), sys.stdin.fileno())
        os.dup2(std_out.fileno(), sys.stdin.fileno())
        os.dup2(std_err.fileno(), sys.stdin.fileno())

    def __init__(self, arguments_dictionary):
        self.arg_d = arguments_dictionary

    def ssh_exec(self, ip, remote_user, local_user, cmd):
        # use the -i identity file option due to ssh forwarding
        # note: for debugging purposes use: "-E /[file_path]"
        ssh_command = "ssh -i /home/{}/.ssh/id_rsa {}@{} sudo {}".format(
                                            local_user, remote_user, ip, cmd)
        process = subprocess.Popen(ssh_command.split(), stdout=subprocess.PIPE)
        stdout, stderr = process.communicate()
        return stdout, stderr, process.returncode

    def exec(self, cmd):
        command = "sudo {} 1>/dev/null 2>&1".format(cmd)
        process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
        stdout, stderr = process.communicate()
        return stdout, stderr, process.returncode

    def netserver_end(self):
        # try graceful end
        self.ssh_exec(self.arg_d["ip_dest_control"], self.arg_d["user_dest"],
                      self.arg_d["user_source"], "kill -2 {}"
                      .format(self.arg_d["netserver_pid"]))
        # resort to kill
        self.ssh_exec(self.arg_d["ip_dest_control"], self.arg_d["user_dest"],
                      self.arg_d["user_source"], "kill {}"
                      .format(self.arg_d["netserver_pid"]))
        # remove pid file
        self.ssh_exec(self.arg_d["ip_dest_control"], self.arg_d["user_dest"],
                      self.arg_d["user_source"], "rm /tmp/net-applet-shuffler/#"
                        "netserver_{}".format(self.arg_d["applet_id"],
                                              self.arg_d["netserver_pid"]))
        return True

    def netserver_start(self):
        # pid of netserver which is about to be started
        netserver_pid = "0"
        # netperf needs a netserver at dest listening on a specific port (
        # control port)
        _, _, exit_code = self.ssh_exec(self.arg_d["ip_dest_control"],
                                        self.arg_d["user_dest"],
                                        self.arg_d["user_source"],
                                        "netserver -4 -p {}"
                                        .format(self.arg_d["netserver_port"]))
        # in case of error, there is a netserver possibly already running
        if exit_code != 0:
            print("error: netserver (required for netperf) could not be "
                  "started at {}\n".format(self.arg_d["name_dest"]))
            return False
        # get the process id of the just started netserver != pid of ssh.exec
        # process
        # Note: "pgrep netserver" does not work, since we want to get a
        # specific one
        stdout = self.ssh_exec(self.arg_d["ip_dest_control"],
                               self.arg_d["user_dest"],
                               self.arg_d["user_source"],
                               "ps -ef | grep netserver")
        stdout_decoded = stdout[0].decode("utf-8")
        for line in stdout_decoded.splitlines():
            # unique identifier
            if "netserver -4 -p {}".format(self.arg_d["netserver_port"]) in line:
                netserver_pid = line.split()[1]
        # save netserver pid to /tmp/net-applet-shuffler/netserver_[pid] at dst
        self.arg_d["netserver_pid"] = netserver_pid
        self.ssh_exec(self.arg_d["ip_dest_control"], self.arg_d["user_dest"],
                      self.arg_d["user_source"],
                      "touch /tmp/net-applet-shuffler/netserver_{}"
                      .format(self.arg_d["applet_id"]))
        self.ssh_exec(self.arg_d["ip_dest_control"], self.arg_d["user_dest"],
                      self.arg_d["user_source"], "sh -c \"echo '{}' > "
                      "/tmp/net-applet-shuffler/netserver_{}\"".format(
                      self.arg_d["netserver_pid"], self.arg_d["applet_id"]))
        return True

    def test_running(self, starting):
        # due to network congestion, this might fail, thus has to be robust
        done = False
        while not done:
            try:
                # while the following file exists, there is a ongoing transfer
                if starting:
                    self.exec("touch /tmp/net-applet-shuffler/running_{}"
                              .format(self.arg_d["applet_id"]))
                if not starting:
                    self.exec("rm /tmp/net-applet-shuffler/running_{}"
                              .format(self.arg_d["applet_id"]))
                return True
            except subprocess.SubprocessError:
                pass

    def main(self):
        # demonize program
        self.demonize_program()
        # make sure necessary dirs exist, local and remote
        self.exec("mkdir /tmp/net-applet-shuffler")
        # redirect output to file
        sys.stdout = open("/tmp/net-applet-shuffler/netperf_controller_stdout",
                          "w")
        sys.stderr = open("/tmp/net-applet-shuffler/netperf_controller_stderr",
                          "w")
        self.ssh_exec(self.arg_d["ip_dest_control"], self.arg_d["user_dest"],
                      self.arg_d["user_source"],
                      "mkdir /tmp/net-applet-shuffler")
        # write test in progress file
        # to be checked if there are ongoing transfers
        self.test_running(True)
        # start netserver on destination
        netserver_started = self.netserver_start()
        # return false if netserver could not be started
        if not netserver_started:
            sys.exit(2)
        # start netperf as blocking process (note, this is an independent
        # thread)
        # try 10 times, since due to network congestion tries might be
        # here, traffic flows from source to destination (program runner is
        # source)
        # netperf -H [dest_ip],[ipv4] -L [source_ip],[ipv4] -p [
        # netserver_control_port] -l [flow_length: bytes(<0) or seconds(>0)] -s
        # [seconds_to_wait_before_test] -- -P [port_source],[port_dest] -T [
        # protocol] -4
        amount_tries = 0
        netperf_start_failed = True
        while amount_tries < 10:
            netperf_cmd = "netperf -H {},4 -L {},4 -p {} -l {} -s {} -- -P {}" \
                          ",{} -T TCP -4".format(self.arg_d["ip_dest_test"],
                                                 self.arg_d["ip_source_test"],
                                                 self.arg_d["netserver_port"],
                                                 self.arg_d["test_length"],
                                                 self.arg_d["flow_offset"],
                                                 self.arg_d["port_source"],
                                                 self.arg_d["port_dest"])
            _, _, exit_code = self.exec(netperf_cmd)
            if exit_code == 0:
                netperf_start_failed = False
                break
            amount_tries += 1
        # if netperf could not be started
        if netperf_start_failed:
            print("error: netperf performance test could not be executed\n"
                  "failed params:\n")
            print("netperf -H {},4 -L {},4 -p {} -l {} -s {} -- -P {},{} -T "
                  "TCP -4\n".format(self.arg_d["ip_dest_test"],
                    self.arg_d["ip_source_test"], self.arg_d["netserver_port"],
                    self.arg_d["test_length"], self.arg_d["flow_offset"],
                    self.arg_d["port_source"], self.arg_d["port_dest"]))
            sys.exit(3)

        self.test_running(False)
        self.netserver_end()
        print("netperf-controller ended gracefully")
        sys.exit(0)


if __name__ == '__main__':

    # arguments dictionary
    arg_d = dict()
    arg_d["applet_id"] = sys.argv[1]
    arg_d["name_source"] = sys.argv[2]
    arg_d["user_source"] = sys.argv[3]
    arg_d["ip_source_test"] = sys.argv[4]
    arg_d["port_source"] = sys.argv[5]
    arg_d["name_dest"] = sys.argv[6]
    arg_d["user_dest"] = sys.argv[7]
    arg_d["ip_dest_test"] = sys.argv[8]
    arg_d["port_dest"] = sys.argv[9]
    arg_d["netserver_port"] = sys.argv[10]
    arg_d["test_length"] = sys.argv[11]
    arg_d["flow_offset"] = sys.argv[12]
    arg_d["ip_source_control"] = sys.argv[13]
    arg_d["ip_dest_control"] = sys.argv[14]
    # init
    net_cont = NetperfController(arg_d)
    net_cont.main()
