#!/usr/bin/python3
#
# Email: Hagen Paul Pfeifer <hagen@jauu.net>

import importlib.util
import json
import optparse
import os
import pprint
import subprocess
import sys


pp = pprint.PrettyPrinter(indent=4)

__program__ = "net-applet-shuffler"
__version__ = "1"


class Printer:

    STD = 0
    VERBOSE = 1

    def __init__(self, verbose=False):
        self.verbose = verbose

    def err(self, msg):
        sys.stderr.write(msg)

    def msg(self, msg, level=VERBOSE, underline=False):
        if level == Printer.VERBOSE and not self.verbose:
            return
        prefix = "  #   " if level == Printer.VERBOSE else ""
        if not underline:
            return sys.stdout.write(prefix + msg) - 1
        else:
            str_len = len(prefix + msg)
            sys.stdout.write(prefix + msg)
            self.msg("\n" + '=' * str_len + "\n")

    def set_verbose(self):
        pass


class Ssh:

    def __init__(self):
        pass

    def exec(self, ip, user, cmd):
        full = "ssh {}@{} sudo {} 1>/dev/null 2>&1".format(user, ip, cmd)
        p = subprocess.Popen(full.split(), stdout=subprocess.PIPE)
        p.communicate()
        return p.returncode

    def exec_verbose(self, ip, user, cmd):
        full = "ssh {}@{} sudo {}".format(user, ip, cmd)
        p = subprocess.Popen(full.split(), stdout=subprocess.PIPE)
        stdout, stderr = p.communicate()
        return stdout, stderr, p.returncode

    def _copy(self, remote_user, remote_ip, remote_path, local_path, to_local):
        cmd = str()
        if to_local:
            cmd = "scp {}@{}:{} {}".format(remote_user, remote_ip,
                                           remote_path, local_path)
        else:
            cmd = "scp {} {}@{}:{}".format(local_path, remote_user,
                                           remote_ip, remote_path)
        p = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
        stdout, stderr = p.communicate()
        return stdout, stderr, p.returncode

    def _exec_locally(self, cmd):
        cmd = "sudo " + cmd
        process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
        stdout, stderr = process.communicate()
        return stdout, stderr, process.returncode

    # e.g. path: "/tmp/net-applet-shuffler"
    # filename: "tcp_dump.file"
    def copy_from(self, remote_user, remote_ip, from_path, to_path,
                  source_filename, dest_filename):
        # due to permission restrictions, scp can't copy to not user owned
        # places directly
        # note: the local user and ip are not known here
        # 1. temp copy to /tmp
        stdout, stderr, exit_code = self._copy(remote_user, remote_ip,
                os.path.join(from_path, source_filename), "/tmp/temp_f", True)
        # 2. make target dir
        cmd = "mkdir -p {}".format(to_path)
        self._exec_locally(cmd)
        # 3. copy to target location
        cmd = "cp /tmp/temp_f {}/{}".format(to_path, dest_filename)
        self._exec_locally(cmd)
        # 4. remove temp copy
        cmd = "rm -f /tmp/temp_f"
        self._exec_locally(cmd)
        return stdout, stderr, exit_code

    def copy_to(self, user, ip, from_path, to_path, source_filename,
                dest_filename):
        # due to permission restrictions, scp can't copy to not user owned
        # places directly
        # 1. temp copy to tmp
        stdout, stderr, exit_code = self._copy(user, ip, "/tmp/tmp_f",
                                               (from_path + "/" +
                                                source_filename), False)
        # 2. make target dir
        self.exec(ip, user, "mkdir -p {}".format(to_path))
        # 3. copy to target location
        self.exec(ip, user, "cp '/tmp/tmp_f' '{}/{}'".format(to_path,
                                                             dest_filename))
        # 4. remove temp copy
        self.exec(ip, user, "rm -f '/tmp/tmp_f'")
        return stdout, stderr, exit_code


class Exchange:

    def __init__(self):
        self.ssh = Ssh()

    def ping(self, host):
        cmd = "ping -c 1 {} 1>/dev/null 2>&1 ".format(host)
        response = os.system(cmd)
        if response == 0:
            return True
        return False


class Conf:

    def __init__(self):
        hp = os.path.dirname(os.path.realpath(__file__))
        fp = os.path.join(hp, "conf.json")
        with open(fp, 'r') as fd:
            data = fd.read()
            self.data = json.loads(data)

    def __getitem__(self, item):
        pass

    def get_data_ip(self, host_name):
        for host in self.data["boxes"]:
            if host_name == host:
                interfaces = self.data["boxes"][host_name]["interfaces"]
                for interface in interfaces:
                    if interface["type"] == "data":
                        return interface["ip-address"]
        print("error: get_data_ip not found for {}\n".format(host_name))
        sys.exit(1)

    def get_control_ip(self, host_name):
        for host in self.data["boxes"]:
            if host_name == host:
                interfaces = self.data["boxes"][host_name]["interfaces"]
                for interface in interfaces:
                    if interface["type"] == "control":
                        return interface["ip-address"]
        print("error: get_control_ip not found for {}\n".format(host_name))
        sys.exit(1)

    def get_data_iface_name(self, host_name):
        for host in self.data["boxes"]:
            if host_name == host:
                interfaces = self.data["boxes"][host_name]["interfaces"]
                for interface in interfaces:
                    if interface["type"] == "data":
                        return interface["name"]
        print("error: get_data_iface_name not found for {}\n"
              .format(host_name))
        sys.exit(1)

    def get_control_iface_name(self, host_name):
        for host in self.data["boxes"]:
            if host_name == host:
                interfaces = self.data["boxes"][host_name]["interfaces"]
                for interface in interfaces:
                    if interface["type"] == "control":
                        return interface["name"]
        print("error: get_control_iface_name not found for {}\n"
              .format(host_name))
        sys.exit(1)

    def get_data_default_route(self, host_name):
        for host in self.data["boxes"]:
            if host_name == host:
                interfaces = self.data["boxes"][host_name]["interfaces"]
                for interface in interfaces:
                    if interface["type"] == "data":
                        return interface["default-route"]
        print("error: get_data_default_route not found for {}\n"
              .format(host_name))
        sys.exit(1)

    def get_control_default_route(self, host_name):
        for host in self.data["boxes"]:
            if host_name == host:
                interfaces = self.data["boxes"][host_name]["interfaces"]
                for interface in interfaces:
                    if interface["type"] == "control":
                        return interface["default-route"]
        print("error: get_control_default_route not found for {}\n"
              .format(host_name))
        sys.exit(1)

    def get_middle_box_iface_name_by_network_name(self, host_name, network):
        for host in self.data["boxes"]:
            if host_name == host:
                interfaces = self.data["boxes"][host_name]["interfaces"]
                for interface in interfaces:
                    if interface["network-name"] == network:
                        return interface["name"]
        print("error: get_middle_box_iface_name_by_network_name not found for "
              "host {} and network name {}\n".format(host_name, network))
        sys.exit(1)

    def get_all_data_iface_names(self, host_name):
        for host in self.data["boxes"]:
            if host_name == host:
                interfaces = self.data["boxes"][host_name]["interfaces"]
                interface_list = list()
                for interface in interfaces:
                    if interface["type"] == "data":
                        interface_list.append(interface["name"])
                if not interface_list:
                    print("warning: get_all_data_iface_names empty for {}"
                          .format(host_name))
                return interface_list
        print("error: get_all_data_iface_names not possible for host {}"
              .format(host_name))
        sys.exit(1)

    def get_user(self, host_name):
        for host in self.data["boxes"]:
            if host_name == host:
                return self.data["boxes"][host_name]["user"]
        print("error: get_user not found for {}\n".format(host_name))
        sys.exit(1)


class AppletExecuter:

    def __init__(self, external_controlled=False, verbose=False):
        self.verbose = verbose
        self.applet_name = False
        self.p = Printer(verbose=self.verbose)
        if not external_controlled:
            self.parse_local_options()
        self.load_conf()

    def applet_path(self, name):
        hp = os.path.dirname(os.path.realpath(__file__))
        fp = os.path.join(hp, "applets", name)
        if not os.path.exists(fp):
            return None, False
        ffp = os.path.join(fp, "applet.py")
        return ffp, True

    def load_conf(self):
        hp = os.path.dirname(os.path.realpath(__file__))
        fp = os.path.join(hp, "conf.json")
        with open(fp, 'r') as fd:
            data = fd.read()
            self.conf = json.loads(data)

    def parse_local_options(self):
        parser = optparse.OptionParser()
        parser.usage = "Executer"
        parser.add_option("-v", "--verbose", dest="verbose", default=False,
                          action="store_true", help="show verbose")
        self.opts, args = parser.parse_args(sys.argv[0:])

        if len(args) < 3:
            self.p.err("No <applet> argument given, exiting\n")
            sys.exit(1)

        if self.opts.verbose:
            self.p.set_verbose()
        self.applet_name = args[2]
        self.applet_args = args[3:]

    def set_applet_data(self, applet_name, applet_args):
        self.applet_name = applet_name
        self.applet_args = applet_args

    def import_applet_module(self):
        ffp, ok = self.applet_path(self.applet_name)
        if not ok:
            self.p.err("Applet ({}) not available, call list\n"
                       .format(self.applet_name))
            sys.exit(1)

        spec = importlib.util.spec_from_file_location("applet", ffp)
        self.applet = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.applet)

    def run(self):
        if not self.applet_name:
            print("You want to execute an applet but I don't know what applet!")
            print("This is an internal error, see self.external_controlled")
            return False
        self.import_applet_module()
        xchange = Exchange()
        xchange.p = self.p
        # the status is used later for campaigns:
        # if the status is false the campaign must be
        # stopped, if true everything is fine!
        self.p.msg("{}\n".format(self.applet_args),
                   level=Printer.VERBOSE)
        status = self.applet.main(xchange, Conf(), self.applet_args)
        if status:
            return True
        elif not status:
            return False
        else:
            print("Applet defect: MUST return True or False")
            return False


class AppletLister:

    def __init__(self, verbose=False):
        self.verbose = verbose
        self.p = Printer(verbose=self.verbose)

    def subdirs(self, d):
        return [name for name in os.listdir(d) if os.path.isdir(os.path.join(d, name))]

    def run(self):
        hp = os.path.dirname(os.path.realpath(__file__))
        fp = os.path.join(hp, "applets")
        dirs = self.subdirs(fp)
        self.p.msg("Available applets:\n", level=Printer.STD)
        for d in dirs:
            self.p.msg("  {}\n".format(d), level=Printer.STD)


class CampaignExecuter:

    def __init__(self, verbose=False):
        self.verbose = verbose
        self.p = Printer(verbose=self.verbose)
        self.parse_local_options()

    def campaign_path(self, name):
        hp = os.path.dirname(os.path.realpath(__file__))
        fp = os.path.join(hp, "campaigns", name)
        if not os.path.exists(fp):
            self.p.msg("Campaign path \"{}\" does not exist".format(fp),
                       level=Printer.STD)
            return None, False
        ffp = os.path.join(fp, "run.py")
        return ffp, True

    def parse_local_options(self):
        parser = optparse.OptionParser()
        parser.usage = "Executer"
        parser.add_option("-v", "--verbose", dest="verbose", default=False,
                          action="store_true", help="show verbose")
        self.opts, args = parser.parse_args(sys.argv[0:])

        if len(args) < 3:
            self.p.err("No <campaign> argument given, exiting\n")
            sys.exit(1)

        if self.opts.verbose:
            self.p.set_verbose()
        self.campaign_name = args[2]

    def execute_applet(self, applet):
        applet_name = applet.split()[0]
        applet_args = applet.split()[1:]
        sys.stdout.write(" - {}\n".format(applet_name))
        app_executer = AppletExecuter(external_controlled=True,
                                      verbose=self.verbose)
        app_executer.set_applet_data(applet_name, applet_args)
        app_status = app_executer.run()
        if not app_status:
            print("Applet returned negative return code, stopping campaign now")
            sys.exit(1)

    def import_campaign_module(self):
        ffp, ok = self.campaign_path(self.campaign_name)
        if not ok:
            self.p.err("Applet ({}) not available, call list\n"
                       .format(self.campaign_name))
            sys.exit(1)

        spec = importlib.util.spec_from_file_location("campaign", ffp)
        self.campaign = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.campaign)
        return ffp

    def parse_campaign(self):
        self.path, ok = self.campaign_path(self.campaign_name)
        if not ok:
            print("Campaign \"{}\" not valid".format(self.campaign_name))
            return None, False
        return True, True

    def run(self):
        data, ok = self.parse_campaign()
        if not ok:
            sys.exit(1)
        self.p.msg("Execute Campaign \"{}\"\n".format(self.campaign_name),
                   level=Printer.STD)
        self.import_campaign_module()
        # ssh class and ping
        xchange = Exchange()
        # printer (p.msg)
        xchange.p = self.p
        # applet name and args, creates AppletExecuter() and calls its run
        xchange.exec = self.execute_applet
        # starts the campaign run
        self.campaign.main(xchange)


class CampaignLister:

    def __init__(self, verbose=False):
        self.verbose = verbose
        self.p = Printer(verbose=self.verbose)

    def subdirs(self, d):
        return [name for name in os.listdir(d) if os.path.isdir(os.path.join(d, name))]

    def run(self):
        hp = os.path.dirname(os.path.realpath(__file__))
        fp = os.path.join(hp, "campaigns")
        dirs = self.subdirs(fp)
        sys.stdout.write("Available campaigns:\n")
        for d in dirs:
            sys.stdout.write("  {}\n".format(d))


class NetAppletShuffler:

    modes = {
       "exec-applet":    ["AppletExecuter",   "Execute applets"],
       "list-applets":   ["AppletLister",     "List all applets"],
       "exec-campaign":  ["CampaignExecuter", "Execute campaign"],
       "list-campaigns": ["CampaignLister",   "List all campaigns"]
            }

    def __init__(self):
        self.verbose = False

    def which(self, program):
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            full_path = os.path.join(path, program)
            if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                return full_path
        return None

    def print_version(self):
        sys.stdout.write("%s\n" % __version__)

    def print_usage(self):
        sys.stderr.write("Usage: nas [-h | --help]" +
                         " [--version]" +
                         " <applet> [<applet-options>]\n")

    def print_modules(self):
        for i in NetAppletShuffler.modes.keys():
            sys.stderr.write("   %-15s - %s\n" % (i, NetAppletShuffler.modes[i][1]))

    def args_contains(self, argv, *cmds):
        for cmd in cmds:
            for arg in argv:
                if arg == cmd:
                    return True
        return False

    def parse_global_options(self):
        if len(sys.argv) <= 1:
            self.print_usage()
            sys.stderr.write("Available applets:\n")
            self.print_modules()
            return None

        self.binary_path = sys.argv[-1]

        # --version can be placed somewhere in the
        # command line and will evaluated always: it is
        # a global option
        if self.args_contains(sys.argv, "--version"):
            self.print_version()
            return None

        # handle verbose flag
        if "--verbose" in sys.argv:
            sys.argv.remove("--verbose")
            self.verbose = True
        if "-v" in sys.argv:
            self.verbose = True
            sys.argv.remove("-v")

        # -h | --help as first argument is treated special
        # and has other meaning as a submodule
        if self.args_contains(sys.argv[1:2], "-h", "--help"):
            self.print_usage()
            sys.stderr.write("Available modules:\n")
            self.print_modules()
            return None

        submodule = sys.argv[1].lower()
        if submodule not in NetAppletShuffler.modes:
            self.print_usage()
            sys.stderr.write("Modules \"%s\" not known, available modules "
                             "are:\n" % submodule)
            self.print_modules()
            return None

        classname = NetAppletShuffler.modes[submodule][0]
        return classname

    def run(self):
        classtring = self.parse_global_options()
        if not classtring:
            return 1

        classinstance = globals()[classtring](verbose=self.verbose)
        ok = classinstance.run()
        if not ok:
            return 1
        return 0


if __name__ == "__main__":
    try:
        mca = NetAppletShuffler()
        sys.exit(mca.run())
    except KeyboardInterrupt:
        sys.stderr.write("SIGINT received, exiting\n")
