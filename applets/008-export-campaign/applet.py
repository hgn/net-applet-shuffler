
import os


def show_help(x):
    x.p.msg("\n 008-export-campaign:\n", False)
    x.p.msg(" applet for exporting the campaign as file to a folder\n", False)
    x.p.msg("\n usage:\n", False)
    x.p.msg(" - exec 008-export-campaign: [host] campaign_name:\"[string]\" "
            "path:\"[file_descriptor]\"\n", False)
    x.p.msg("\n examples:\n", False)
    x.p.msg(" - exec 008-export-campaign: alpha campaign_name:\"test\" "
            "path:\"./campaign_1\"\n", False)
    x.p.msg(" - exec 008-export-campaign: alpha campaign_name:\"001-test\" "
            "path:\"/home/alpha/bin/net-applet-shuffler/campaigns/test/"
            "campaign.save\"", False)


def print_wrong_usage(x):
    x.p.err("error: wrong usage\n")
    x.p.err("use: [host] "
            "campaign_name:\"[string]\" "
            "path:\"[file_descriptor]\"\n")


def save_campaign_file(x, dic):
    # read campaign path file
    campaign_file_path = os.path.join(os.path.dirname(__file__), "./../../",
                                      "campaigns", dic["campaign_name"],
                                      "run.py")
    print(campaign_file_path)
    campaign_file = open(campaign_file_path, "r")
    campaign_string = campaign_file.read()
    campaign_file.close()
    # make sure target path exists
    x.ssh.exec(dic["host_ip_control"], dic["host_user"],
               "mkdir -p {}".format(dic["file_path"]))
    # save campaign file
    campaign_file = open(os.path.join(dic["file_path"], dic["file_name"]), "w")
    campaign_file.write(campaign_string)
    campaign_file.close()
    return True


def create_file_path(x, dic, file_descriptor):
    file_path = str()
    file_name = str()
    # note: the current file path is two levels below nas
    # relative file path logic
    if not os.path.isabs(file_descriptor):
        current_file_dir = os.path.dirname(__file__)
        # nas file path + dir and filename to dst file
        file_path_full = os.path.join(current_file_dir + "/../../",
                                      file_descriptor)
        file_path, file_name = os.path.split(file_path_full)
    # absolute file path logic
    elif os.path.isabs(file_descriptor):
        file_path, file_name = os.path.split(file_descriptor)

    if not (file_path or file_name):
        x.p.err("error: file path and/or name is/are empty\n")
        return False

    dic["file_path"] = file_path
    dic["file_name"] = file_name

    return True


def main(x, conf, args):
    if "?" in args:
        show_help(x)
        return False
    # arguments dictionary
    info = dict()
    file_descriptor = "/tmp/campaign.save"
    try:
        info["host_name"] = args[0]
        args.remove(info["host_name"])
        for argument in args:
            key = argument.split(":")[0]
            value = argument.split(":")[1]
            if key == "campaign_name":
                info["campaign_name"] = value.strip("\"")
            elif key == "path":
                file_descriptor = value.strip("\"")
            else:
                print_wrong_usage(x)
                return False
    except IndexError:
        print_wrong_usage(x)
        return False

    if not create_file_path(x, info, file_descriptor):
        return False
    info["host_ip_control"] = conf.get_control_ip(info["host_name"])
    info["host_user"] = conf.get_user(info["host_name"])

    if not save_campaign_file(x, info):
        return False

    return True
