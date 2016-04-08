
import os
import subprocess
import sys
import time

from time import strftime


class NetworkController:

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
                sys.exit(0)
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
            self.file_out = open("/tmp/net-applet-shuffler/logs/network_"
                                 "controller_stdout_{}".format(time_now), "w")
            self.file_err = open("/tmp/net-applet-shuffler/logs/network_"
                                 "controller_stderr_{}".format(time_now), "w")
            sys.stdout = self.file_out
            sys.stderr = self.file_err
        if not start:
            self.file_out.close()
            self.file_err.close()
            sys.stdout = self.stdout_save
            sys.stderr = self.stderr_save

    def execute(self, cmd):
        command = "sudo {} 1>/dev/null 2>&1".format(cmd)
        process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
        stdout, stderr = process.communicate()
        exit_code = process.returncode
        print(" - exit code: {} - ".format(exit_code) + command)
        return stdout, stderr, exit_code

    def establish_direct_setup(self):
        self.execute("ip link set dev {} down".format(arg_d["interface"]))
        time.sleep(6)
        self.execute("ip a add {}/16 dev {}".format(arg_d["ip"],
                                                    arg_d["interface"]))
        time.sleep(6)
        self.execute("ip link set dev {} up".format(arg_d["interface"]))

    def establish_indirect_setup(self):
        self.execute("ip link set dev {} down".format(arg_d["interface"]))
        time.sleep(6)
        self.execute("ip a add {}/24 dev {}".format(arg_d["ip"],
                                                    arg_d["interface"]))
        time.sleep(6)
        self.execute("ip link set dev {} up".format(arg_d["interface"]))
        time.sleep(6)
        self.execute("ip r add default via {}".format(arg_d["default_route"]))

    def main(self):
        self.demonize_program()
        # make sure necessary dirs exist, local and remote
        self.execute("mkdir /tmp/net-applet-shuffler")
        self.execute("mkdir /tmp/net-applet-shuffler/logs")
        # redirect output to file
        self.redirect_console_output(True)
        # wait, so every instance can be started before the network goes down
        time.sleep(4)
        if arg_d["setup"] == "direct":
            print(" - establishing direct setup")
            self.establish_direct_setup()
        elif arg_d["setup"] == "indirect":
            print(" - establishing indirect setup")
            self.establish_indirect_setup()
        else:
            # this should not happen
            sys.exit(1)
        print(" - network-controller ended gracefully")
        self.redirect_console_output(False)
        sys.exit(0)


if __name__ == '__main__':

    # arguments dictionary
    arg_d = dict()
    arg_d["setup"] = sys.argv[1]
    arg_d["interface"] = sys.argv[2]
    arg_d["ip"] = sys.argv[3]
    arg_d["default_route"] = sys.argv[4]
    # init
    net_cont = NetworkController(arg_d)
    net_cont.main()
