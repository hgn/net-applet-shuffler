
import os


def print_usage(x):
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


def save_campaign_file(x, dic):
    # read campaign path file
    campaign_file_path = os.path.join(os.path.dirname(__file__), "./../../",
                                      "campaigns", dic["campaign_name"],
                                      "run.py")
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


def create_file_path(x, file_descriptor, absolute, dic):
    file_path = str()
    file_name = str()
    # note: the current file path is two levels below nas
    # path and file name shuffling magic
    if not absolute:
        current_file_dir = os.path.dirname(__file__)
        # nas file path + dir and filename to dst file
        file_path_full = os.path.join(current_file_dir + "/../../",
                                      file_descriptor)
        file_path_split = file_path_full.split("/")
        file_name = file_path_split[len(file_path_split) - 1]
        file_path_split.pop(len(file_path_split) - 1)
        file_path = "/".join(file_path_split)
    # absolute file path logic
    elif absolute:
        file_path_split = file_descriptor.split("/")
        file_name = file_path_split[len(file_path_split) - 1]
        try:
            file_path_split.pop(len(file_path_split) - 1)
            file_path = "/".join(file_path_split)
        except IndexError:
            # this means the top directory is used
            # will throw a permission denied anyways
            file_path = "/"

    if not (file_path or file_name):
        x.p.err("error: file path and/or name is/are empty\n")
        return False

    dic["file_path"] = file_path
    dic["file_name"] = file_name

    return True


def main(x, conf, args):
    if "?" in args:
        print_usage(x)
        return False
    # arguments dictionary
    dic = dict()
    is_file_path_absolute = True
    try:
        dic["host_name"] = args[0]
        dic["campaign_name"] = args[1].split(":").strip("\"")
        file_descriptor = args[2].split(":")[1].strip("\"")
        if file_descriptor[0] == "/":
            is_file_path_absolute = True
        else:
            is_file_path_absolute = False
    except IndexError:
        x.p.err("error: wrong usage\n")
        return False

    if not create_file_path(x, file_descriptor, is_file_path_absolute, dic):
        return False
    dic["host_ip_control"] = conf.get_control_ip(dic["host_name"])
    dic["host_user"] = conf.get_user(dic["host_name"])

    if not save_campaign_file(x, dic):
        return False

    return True
