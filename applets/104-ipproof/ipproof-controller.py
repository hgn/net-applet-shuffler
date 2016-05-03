
import os
import sys
import subprocess
import time

from threading import Thread


class IpproofController:

    IPPROOF_SERVER_NAME = "ipproof-server"
    output_redirected = False

    def __init__(self, arguments_dictionary, ipproof_server_name):
        self.stdout_save = sys.stdout
        self.stderr_save = sys.stderr
        self.dic = arguments_dictionary
        self.IPPROOF_SERVER_NAME = ipproof_server_name

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
            time_now = time.strftime("%H_%M_%S")
            self.file_out = open("/tmp/net-applet-shuffler/logs/ipproof_"
                                 "controller_stdout_{}".format(time_now), "w")
            self.file_err = open("/tmp/net-applet-shuffler/logs/ipproof_"
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

    def ipproof_server_end(self):
        # try graceful end
        _, _, exit_code = self.ssh_exec(self.dic["ip_dest_control"],
                                        self.dic["user_dest"],
                                        self.dic["user_source"],
                                        "kill -2 {}".format(
                                            self.dic["ipproof_pid"]))
        if exit_code == 0:
            # remove pid file
            self.ssh_exec(self.dic["ip_dest_control"],
                          self.dic["user_dest"], self.dic["user_source"],
                          "rm /tmp/net-applet-shuffler/ipproof_{}"
                          .format(self.dic["applet_id"],
                                  self.dic["ipproof_pid"]))
        return True

    def _server_start_thread(self):
        self.ssh_exec(self.dic["ip_dest_control"], self.dic["user_dest"],
                      self.dic["user_source"], "{} -4 -p {}"
                      .format(dic["ipproof_server_path"],
                              self.dic["ipproof_port"]))

    def ipproof_server_start(self):
        ipproof_pid = "0"
        server_thread = Thread(target=self._server_start_thread, args=())
        server_thread.daemon = True
        server_thread.start()
        time.sleep(1)
        stdout = self.ssh_exec(self.dic["ip_dest_control"],
                               self.dic["user_dest"],
                               self.dic["user_source"],
                               "ps -ef | grep {}".format(
                                   self.IPPROOF_SERVER_NAME))
        stdout_decoded = stdout[0].decode("utf-8")
        for line in stdout_decoded.splitlines():
            # unique identifier
            if "{} -4 -p {}".format(self.IPPROOF_SERVER_NAME,
                                    self.dic["ipproof_port"]) in line:
                ipproof_pid = line.split()[1]
                break
        if ipproof_pid == "0":
            print("warning (no abort): ipproof server pid could not be "
                  "retrieved")
        self.dic["ipproof_pid"] = ipproof_pid
        self.ssh_exec(self.dic["ip_dest_control"], self.dic["user_dest"],
                      self.dic["user_source"],
                      "touch /tmp/net-applet-shuffler/ipproof_{}"
                      .format(self.dic["applet_id"]))
        self.ssh_exec(self.dic["ip_dest_control"], self.dic["user_dest"],
                      self.dic["user_source"], "sh -c \"echo '{}' > "
                      "/tmp/net-applet-shuffler/ipproof_{}\"".format(
                      self.dic["ipproof_pid"], self.dic["applet_id"]))
        return True

    def test_running(self, starting):
        # due to network congestion, this might fail, thus has to be robust
        done = False
        while not done:
            try:
                # while the following file exists, there is a ongoing transfer
                if starting:
                    self.execute("touch /tmp/net-applet-shuffler/running_{}"
                                 .format(self.dic["applet_id"]))
                if not starting:
                    self.execute("rm /tmp/net-applet-shuffler/running_{}"
                                 .format(self.dic["applet_id"]))
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
        self.ssh_exec(self.dic["ip_dest_control"], self.dic["user_dest"],
                      self.dic["user_source"],
                      "mkdir -p /tmp/net-applet-shuffler")
        # write test in progress file
        # to be checked if there are ongoing transfers
        self.test_running(True)
        ipproof_started = self.ipproof_server_start()
        if not ipproof_started:
            sys.exit(2)
        amount_tries = 0
        ipproof_start_failed = True
        ipproof_cmd = ""
        while amount_tries < 10:
            print(" - trying to start ipproof")
            ipproof_cmd = "{} -4 -e {} -p {} -t tcp -s {} -n {} -r {} -i " \
                          "{}".format(dic["ipproof_client_path"],
                                      self.dic["ip_dest_data"],
                                      self.dic["ipproof_port"],
                                      self.dic["transfer_size"],
                                      self.dic["iterations"],
                                      self.dic["ack_size"],
                                      self.dic["inter_send_interval"])
            _, _, exit_code = self.execute(ipproof_cmd)
            if exit_code == 0:
                ipproof_start_failed = False
                break
            amount_tries += 1
            time.sleep(1)
        if ipproof_start_failed:
            print("error: ipproof performance test could not be executed\n"
                  "failed params:")
            print(ipproof_cmd + "\n")
            sys.exit(3)

        time.sleep(2)
        print(" - ipproof ended")
        self.test_running(False)
        self.ipproof_server_end()
        print(" - ipproof-controller ended gracefully\n")
        self.redirect_console_output(False)
        sys.exit(0)


if __name__ == '__main__':

    # arguments dictionary
    dic = dict()
    dic["applet_id"] = sys.argv[1]
    dic["user_source"] = sys.argv[2]
    dic["name_dest"] = sys.argv[3]
    dic["user_dest"] = sys.argv[4]
    dic["ip_dest_data"] = sys.argv[5]
    dic["ip_dest_control"] = sys.argv[6]
    dic["ipproof_port"] = sys.argv[7]
    dic["transfer_size"] = sys.argv[8]
    dic["iterations"] = sys.argv[9]
    dic["ack_size"] = sys.argv[10]
    dic["inter_send_interval"] = sys.argv[11]
    dic["ipproof_client_path"] = sys.argv[12]
    dic["ipproof_server_path"] = sys.argv[13]
    ipproof_server_path_split = dic["ipproof_server_path"].split("/")
    ipproof_server_name = ipproof_server_path_split[
        len(ipproof_server_path_split)-1]
    # init
    ip_cont = IpproofController(dic, ipproof_server_name)
    ip_cont.main()
