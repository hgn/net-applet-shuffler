
import os
import subprocess
import sys
import time


class NetworkController:

    def __init__(self, arguments_dictionary):
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

    def execute(self, cmd):
        command = "sudo {}".format(cmd)
        process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
        stdout, stderr = process.communicate()
        return stdout, stderr, process.returncode

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
        # wait, so every instance can be started before the network goes down
        time.sleep(6)
        if arg_d["setup"] == "direct":
            self.establish_direct_setup()
        elif arg_d["setup"] == "indirect":
            self.establish_indirect_setup()
        else:
            # this should not happen
            sys.exit(1)


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
