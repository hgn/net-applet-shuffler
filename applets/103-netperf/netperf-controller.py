
import os
import sys
import subprocess

from time import strftime


class NetperfController:

    output_redirected = False

    def __init__(self, arguments_dictionary):
        self.stdout_save = sys.stdout
        self.stderr_save = sys.stderr
        self.arg_d = arguments_dictionary

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

    def redirect_console_output(self, start):
        if start:
            time_now = strftime("%H_%M_%S")
            self.file_out = open("/tmp/net-applet-shuffler/logs/netperf_"
                                 "controller_stdout_{}".format(time_now), "w")
            self.file_err = open("/tmp/net-applet-shuffler/logs/netperf_"
                                 "controller_stderr_{}".format(time_now), "w")
            self.output_redirected = True
            sys.stdout = self.file_out
            sys.stderr = self.file_err
        if not start and self.output_redirected:
            self.file_out.close()
            self.file_err.close()
            sys.stdout = self.stdout_save
            sys.stderr = self.stderr_save
            self.output_redirected = False

    def ssh_exec(self, ip, remote_user, local_user, cmd):
        # due to demonized root program execution, ssh uses root user params
        # use the -i identity file option for the user file
        # use the -o known_hosts file option for the same reason
        # note: for debugging purposes use: "-vvv -E /[file_path]"
        ssh_command = "ssh -i /home/{}/.ssh/id_rsa -o UserKnownHostsFile=" \
                      "/home/{}/.ssh/known_hosts {}@{} sudo {}"\
            .format(local_user, local_user, remote_user, ip, cmd)
        process = subprocess.Popen(ssh_command.split(), stdout=subprocess.PIPE)
        stdout, stderr = process.communicate()
        exit_code = process.returncode
        print(" - exit code: {} - ".format(exit_code) + ssh_command)
        return stdout, stderr, exit_code

    def execute(self, cmd):
        command = "sudo {}".format(cmd)
        process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
        stdout, stderr = process.communicate()
        exit_code = process.returncode
        print(" - exit code: {} - ".format(exit_code) + command)
        return stdout, stderr, exit_code

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
                      self.arg_d["user_source"], "rm /tmp/net-applet-shuffler/"
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
                    self.execute("touch /tmp/net-applet-shuffler/running_{}"
                                 .format(self.arg_d["applet_id"]))
                if not starting:
                    self.execute("rm /tmp/net-applet-shuffler/running_{}"
                                 .format(self.arg_d["applet_id"]))
                return True
            except subprocess.SubprocessError:
                pass

    def main(self):
        # demonize program
        self.demonize_program()
        # make sure necessary dirs exist, local and remote
        self.execute("mkdir -p /tmp/net-applet-shuffler")
        self.execute("mkdir -p /tmp/net-applet-shuffler/logs")
        # redirect output to file
        self.redirect_console_output(True)
        self.ssh_exec(self.arg_d["ip_dest_control"], self.arg_d["user_dest"],
                      self.arg_d["user_source"],
                      "mkdir -p /tmp/net-applet-shuffler")
        # write test in progress file
        # to be checked if there are ongoing transfers
        self.test_running(True)
        # start netserver on destination
        netserver_started = self.netserver_start()
        # return false if netserver could not be started
        if not netserver_started:
            sys.exit(2)
        # - start netperf as blocking process (note, this is an independent
        # thread)
        # - try 10 times, since due to network congestion tries might be lost
        # - here, traffic flows from source to destination (program runner is
        # source)
        # - note: there is not really a way to transfer x amount of bytes
        # - netperf -H [dest_ip],[ipv4] -L [source_ip],[ipv4] -p [
        # netserver_control_port] -l [flow_length: bytes(<0) or seconds(>0)] -s
        # [seconds_to_wait_before_test] -- -P [port_source],[port_dest] -T [
        # protocol] -4 -m [packet_send_size: bytes] 1500
        amount_tries = 0
        netperf_start_failed = True
        while amount_tries < 10:
            print(" - trying to start netperf")
            netperf_cmd = "netperf -H {},4 -L {},4 -p {} -l {} -s {} -- -P {}"\
                          ",{} -T TCP -4 -m 1500"\
                          .format(self.arg_d["ip_dest_data"],
                                  self.arg_d["ip_source_data"],
                                  self.arg_d["netserver_port"],
                                  self.arg_d["test_length"],
                                  self.arg_d["flow_offset"],
                                  self.arg_d["port_source"],
                                  self.arg_d["port_dest"])
            _, _, exit_code = self.execute(netperf_cmd)
            if exit_code == 0:
                netperf_start_failed = False
                break
            amount_tries += 1
        # if netperf could not be started
        if netperf_start_failed:
            print("error: netperf performance test could not be executed\n"
                  "failed params:\n")
            print("netperf -H {},4 -L {},4 -p {} -l {} -s {} -- -P {},{} -T "
                  "TCP -4 -m 1500\n".format(self.arg_d["ip_dest_data"],
                                            self.arg_d["ip_source_data"],
                                            self.arg_d["netserver_port"],
                                            self.arg_d["test_length"],
                                            self.arg_d["flow_offset"],
                                            self.arg_d["port_source"],
                                            self.arg_d["port_dest"]))
            sys.exit(3)

        print(" - netperf ended")
        self.test_running(False)
        self.netserver_end()
        print(" - netperf-controller ended gracefully")
        self.redirect_console_output(False)
        sys.exit(0)


if __name__ == '__main__':

    # arguments dictionary
    arg_d = dict()
    arg_d["applet_id"] = sys.argv[1]
    arg_d["name_source"] = sys.argv[2]
    arg_d["user_source"] = sys.argv[3]
    arg_d["ip_source_data"] = sys.argv[4]
    arg_d["port_source"] = sys.argv[5]
    arg_d["name_dest"] = sys.argv[6]
    arg_d["user_dest"] = sys.argv[7]
    arg_d["ip_dest_data"] = sys.argv[8]
    arg_d["port_dest"] = sys.argv[9]
    arg_d["netserver_port"] = sys.argv[10]
    arg_d["test_length"] = sys.argv[11]
    arg_d["flow_offset"] = sys.argv[12]
    arg_d["ip_source_control"] = sys.argv[13]
    arg_d["ip_dest_control"] = sys.argv[14]
    # init
    net_cont = NetperfController(arg_d)
    net_cont.main()
