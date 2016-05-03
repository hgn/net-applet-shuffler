"""Applet for using ipproof for data connection and transfer.

"""

import os
import time

from threading import Thread

CONTROLLER_NAME = "ipproof-controller.py"
# fix for exec-applet
CONTROLLER_STARTED = False
LOCAL_PATH = os.path.dirname(os.path.realpath(__file__))
REMOTE_PATH = "/tmp/net-applet-shuffler"


def print_usage(x):
    x.p.msg("\n 104-ipproof:\n", False)
    x.p.msg(" applet for establishing a connection and transferring data from "
            "a source to a destination, only the target port can be "
            "specified\n", False)
    x.p.msg("\n usage:\n", False)
    x.p.msg(" - exec 104-ipproof [host] "
            "sink:[host] "
            "id:[string] "
            "ipproof-client:[file_descriptor] "
            "ipproof-server:[file_descriptor] "
            "[server-port:[number]] "
            "[transfer-size:[byte]] "
            "[iterations:[number]] "
            "[ack-size:[byte]] "
            "[inter-send-interval:[us]]\n", False)
    x.p.msg("\n examples:\n", False)
    x.p.msg(" - exec-applet 104-ipproof alpha sink:beta id:42 ipproof-client:"
            "/home/tcp1/bin/ipproof/unix/ipproof-client ipproof-server:"
            "/home/beta/bin/ipproof/unix/ipproof-server\n", False)
    x.p.msg(" - exec-applet 104-ipproof beta sink:alpha id:42 ipproof-client:"
            "/home/beta/bin/ipproof/unix/ipproof-client ipproof-server:"
            "/home/tcp1/bin/ipproof/unix/ipproof-server server-port:30000 "
            "transfer-size:30000 iterations:1 ack-size:50 "
            "inter-send-interval:25\n", False)


def print_wrong_usage(x):
    x.p.err("error: wrong usage\n")
    x.p.err("use: [host] "
            "sink:[host] "
            "id:[string] "
            "ipproof-client:[file_descriptor] "
            "ipproof-server:[file_descriptor] "
            "[server-port:[number]] "
            "[transfer-size:[byte]] "
            "[iterations:[number]] "
            "[ack-size:[byte]] "
            "[inter-send-interval:[us]]\n")


def controller_thread(x, dic):
    # assemble arguments
    # 1. applet_id
    # 2. user_source
    # 3. name_dest
    # 4. user_dest
    # 5. ip_dest_data
    # 6. ip_dest_control
    # 7. ipproof_port
    # 8. transfer_size
    # 9. iterations
    # 10. ack_size
    # 11. inter_send_interval
    # 12. ipproof_client_path
    # 13. ipproof_server_path
    arguments_string = " ".join((dic["applet_id"],
                                 dic["user_source"],
                                 dic["name_dest"],
                                 dic["user_dest"],
                                 dic["ip_dest_data"],
                                 dic["ip_dest_control"],
                                 dic["ipproof_port"],
                                 dic["transfer_size"],
                                 dic["iterations"],
                                 dic["ack_size"],
                                 dic["inter_send_interval"],
                                 dic["ipproof_client_path"],
                                 dic["ipproof_server_path"]))
    # check if ipproof controller is already on source
    exit_code = x.ssh.exec(dic["ip_source_control"], dic["user_source"],
                           "test -f {}/{}".format(REMOTE_PATH,
                                                  CONTROLLER_NAME))
    # if not, copy it to source
    if not exit_code == 0:
        x.ssh.copy_to(dic["user_source"], dic["ip_source_control"],
                      LOCAL_PATH, REMOTE_PATH, CONTROLLER_NAME,
                      CONTROLLER_NAME)

    x.ssh.exec(dic["ip_source_control"], dic["user_source"],
               "python3.5 {}/{} {}".format(REMOTE_PATH, CONTROLLER_NAME,
                                           arguments_string))
    global CONTROLLER_STARTED
    CONTROLLER_STARTED = True


def ipproof_path_tests(x, dic):
    exit_code = x.ssh.exec(dic["ip_source_control"], dic["user_source"],
                           "test -f {}".format(dic["ipproof_client_path"]))
    if not exit_code == 0:
        x.p.err("error: ipproof client not found\n")
        x.p.err("failed cmd:\n")
        x.p.err("on {}:{}: test -f {} \n".format(dic["user_source"],
                                                 dic["ip_source_control"],
                                                 dic["ipproof_client_path"]))
        return False

    exit_code = x.ssh.exec(dic["ip_dest_control"], dic["user_dest"],
                           "test -f {}".format(dic["ipproof_server_path"]))
    if not exit_code == 0:
        x.p.err("error: ipproof server not found\n")
        x.p.err("failed cmd:\n")
        x.p.err("on {}:{}: test -f {} \n".format(dic["user_dest"],
                                                 dic["ip_dest_control"],
                                                 dic["ipproof_server_path"]))
        return False

    return True


def main(x, conf, args):
    if "?" in args:
        print_usage(x)
        return False
    if not len(args) >= 5:
        print_wrong_usage(x)
        return False
    # arguments dictionary
    dic = dict()
    # default values
    dic["ipproof_port"] = "13337"
    dic["transfer_size"] = "30000"
    dic["iterations"] = "1"
    dic["ack_size"] = "0"
    dic["inter_send_interval"] = "0"
    try:
        dic["name_source"] = args[0]
        args.remove(dic["name_source"])
        dic["name_dest"] = args[0].split(":")[1]
        args.remove("sink:" + dic["name_dest"])
        dic["applet_id"] = args[0].split(":")[1]
        args.remove("id:" + dic["applet_id"])
        dic["ipproof_client_path"] = args[0].split(":")[1]
        args.remove("ipproof-client:" + dic["ipproof_client_path"])
        dic["ipproof_server_path"] = args[0].split(":")[1]
        args.remove("ipproof-server:" + dic["ipproof_server_path"])
        for argument in args:
            key = argument.split(":")[0]
            value = argument.split(":")[1]
            if key == "server-port":
                dic["ipproof_port"] = value
            elif key == "transfer-size":
                dic["transfer_size"] = value
            elif key == "iterations":
                dic["iterations"] = value
            elif key == "ack-size":
                dic["ack_size"] = value
            elif key == "inter-send-interval":
                dic["inter_send_interval"] = value
            else:
                print_wrong_usage(x)
                return False
    except IndexError:
        print_wrong_usage(x)
        return False
    dic["ip_source_control"] = conf.get_control_ip(dic["name_source"])
    dic["user_source"] = conf.get_user(dic["name_source"])
    dic["ip_dest_data"] = conf.get_data_ip(dic["name_dest"])
    dic["ip_dest_control"] = conf.get_control_ip(dic["name_dest"])
    dic["user_dest"] = conf.get_user(dic["name_dest"])
    # check if ipproof paths are valid
    if not ipproof_path_tests(x, dic):
        return False
    # start ipproof thread
    x.ssh.exec(dic["ip_source_control"], dic["user_source"],
               "mkdir -p /tmp/net-applet-shuffler")
    x.p.msg("Starting ipproof applet on host {}\n".format(dic["user_source"]))
    contr_thread = Thread(target=controller_thread, args=(x, dic, ))
    contr_thread.daemon = True
    contr_thread.start()
    while not CONTROLLER_STARTED:
        time.sleep(1)

    return True
