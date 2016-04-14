# usage: exec 009-network setup:direct host1 host2 host3 ...

import os
import subprocess
import time

from threading import Thread

CONTR_NAME = "network-controller.py"
LOCAL_CONT_PATH = os.path.dirname(os.path.realpath(__file__))
REMOTE_CONT_PATH = "/tmp/net-applet-shuffler"
TIMEOUT = 60


class ControllerStart(Thread):

    host_user = "host_user"
    host_ip_control = "host_ip_control"
    arguments = "arguments"

    def __init__(self, user, ip, arguments):
        Thread.__init__(self)
        self.host_user = user
        self.host_ip_control = ip
        self.arguments = arguments

    def run(self):
        ssh_command = "ssh {}@{} sudo python3.5 {}/{} {}".format(
            self.host_user, self.host_ip_control, REMOTE_CONT_PATH, CONTR_NAME,
            self.arguments)
        process = subprocess.Popen(ssh_command.split(), stdout=subprocess.PIPE)
        process.communicate()


def distribute_network_controller(x, host_user, host_ip_control):
    _, _, exit_code = x.ssh.exec(host_ip_control, host_user, "test -f {}/{}"
                                 .format(REMOTE_CONT_PATH, CONTR_NAME))
    # if exit_code != 0 -> does not exist on host
    if not exit_code == 0:
        x.ssh.copy_to(host_user, host_ip_control, LOCAL_CONT_PATH,
                      REMOTE_CONT_PATH, CONTR_NAME, CONTR_NAME)


def main(x, conf, args):
    if not len(args) > 1:
        x.p.msg("wrong usage. use: setup:[direct|dumbbell] host1 host2 "
                "host3...\n")
        return False

    try:
        setup = args[0].split(":")[1]
    except IndexError:
        x.p.msg("error: wrong usage\n")
        return False
    # arguments for controller on hosts
    host_list = list()
    # read in all host names
    for host_number in range(0, (len(args))):
        name_host = str(args[host_number])
        if "setup:" not in name_host:
            host_list.append(name_host)
    # distribute the network controller program
    for host_name in host_list:
        host_user = conf.get_user(host_name)
        host_ip_control = conf.get_control_ip(host_name)
        distribute_network_controller(x, host_user, host_ip_control)
    x.p.msg("network controllers distributed\n")
    # start the network controllers
    for host_name in host_list:
        host_user = conf.get_user(host_name)
        host_ip_data = conf.get_data_ip(host_name)
        host_ip_control = conf.get_control_ip(host_name)
        host_interface = conf.get_data_iface_name(host_name)
        host_def_route = conf.get_data_default_route(host_name)
        arguments = "{} {} {} {}".format(setup, host_interface, host_ip_data,
                                         host_def_route)
        host_thread = ControllerStart(host_user, host_ip_control, arguments)
        host_thread.daemon = True
        host_thread.start()
    # minimum time a network controller needs before the network is reachable
    start_time = round(time.time())
    x.p.msg("waiting for all hosts to be reachable again\n")
    time.sleep(16)
    # wait for the controllers on their respective hosts to complete the setup
    x.p.msg("starting periodical reachability test\n")
    responding_hosts = list()
    while len(host_list) > 0:
        time.sleep(1)
        for host in host_list:
            host_ip = conf.get_data_ip(host)
            if x.ping(host_ip):
                responding_hosts.append(host)
        for responding_host in responding_hosts:
            host_list.remove(responding_host)
            responding_hosts.remove(responding_host)
        # timeout
        if (start_time + TIMEOUT) < round(time.time()):
            x.p.err("error: timeout occurred\n")
            x.p.err("is the network still up?\n")
            return False

    x.p.msg("setup completed and hosts responding\n")

    return True
