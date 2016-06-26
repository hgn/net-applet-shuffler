
import os
import subprocess


def print_help(x):
    x.p.msg("\n 007-transfer-recursive-dir-ownership:\n", False)
    x.p.msg(" - exec 007-transfer-recursive-dir-ownership user:[user] "
            "directory:\"[file_descriptor]\"\n", False)
    return


def create_file_path(x, file_descriptor):
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

    return file_path, file_name


def main(x, conf, args):
    if "?" in args:
        print_help(x)
        return False
    user = ""
    file_descriptor = ""
    try:
        for argument in args:
            key = argument.split(":")[0]
            value = argument.split(":")[1]
            if key == "user":
                user = value
            elif key == "directory":
                file_descriptor = value.strip("\"")
            else:
                print_help(x)
                return False
    except IndexError:
        print_help(x)
        return False

    directory = create_file_path(x, file_descriptor)[0]
    cmd = "sudo chown -R {} {}".format(user, directory)
    process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
    process.communicate()

    return True
