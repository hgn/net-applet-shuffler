#!/usr/bin/python3
#
# Email: Hagen Paul Pfeifer <hagen@jauu.net>


import sys
import os
import optparse
import pprint
import time
import importlib.util
import json
import subprocess


pp = pprint.PrettyPrinter(indent=4)

__programm__ = "net-applet-shuffler"
__version__  = "1"


class Printer:

    STD = 0
    VERBOSE = 1

    def __init__(self, verbose=False):
        self.verbose = verbose

    def err(self, msg):
        sys.stderr.write(msg)

    def msg(self, msg, level=VERBOSE, underline=False):
        if level == Printer.VERBOSE and self.verbose == False:
            return
        prefix = "  #   " if level == Printer.VERBOSE else ""
        if underline == False:
            return sys.stdout.write(prefix + msg) - 1
        else:
            str_len = len(prefix + msg)
            sys.stdout.write(prefix + msg)
            self.msg("\n" + '=' * str_len + "\n")

    def set_verbose(self):
        pass


class Ssh():

    def __init__(self):
        pass

    def exec(self, ip, user, cmd):
        full = "ssh {}@{} sudo {}".format(user, ip, cmd)
        p = subprocess.Popen(full.split(), stdout=subprocess.PIPE)
        stdout, stderr = p.communicate()
        return stdout, stderr, p.returncode

    def _copy(self, remote_user, remote_ip, remote_path, local_path, to_local):
        command = str()
        if to_local:
            command = "scp {}@{}:{} {}".format(remote_user, remote_ip,
                                               remote_path, local_path)
        else:
            command = "scp {} {}@{}:{}".format(local_path, remote_user,
                                               remote_ip, remote_path)
        p = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
        stdout, stderr = p.communicate()
        return stdout, stderr, p.returncode

    # e.g. path: "/tmp/net-applet-shuffler"
    # filename: "tcp_dump.file"
    def copy_from(self, user, ip, from_path, to_path, source_filename,
                  dest_filename):
        stdout, stderr, exit_code = self._copy(user, ip, from_path + "/" +
                source_filename, to_path + "/" + dest_filename, True)
        return stdout, stderr, exit_code

    def copy_to(self, user, ip, from_path, to_path, source_filename,
                dest_filename):
        # due to permission restrictions, scp can't copy to not user owned
        # places directly
        # 1. temp copy to user home
        stdout, stderr, exit_code = self._copy(user, ip, "/home/{}/tmp_f".format(user),
                   (from_path + "/" + source_filename), False)
        # 2. make target dir
        self.exec(ip, user, "mkdir {} 1>/dev/null 2>&1".format(to_path))
        # 3. copy to target location
        self.exec(ip, user, "cp /home/{}/tmp_f {}/{}".format(user, to_path,
                                                             dest_filename))
        # 4. remove temp copy
        self.exec(ip, user, "rm -f /home/{}/tmp_f".format(user))
        return stdout, stderr, exit_code


class Exchange():

    def __init__(self):
        self.ssh = Ssh()

    def ping(self, host):
        cmd = "ping -c 1 {} 1>/dev/null 2>&1 ".format(host)
        response = os.system(cmd)
        if response == 0:
            return True
        return False


class Conf():

    def __init__(self):
        hp = os.path.dirname(os.path.realpath(__file__))
        fp = os.path.join(hp, "conf.json")
        with open(fp, 'r') as fd:
            data = fd.read()
            self.data = json.loads(data)

    def __getitem__(self, item):
        pass

    def get_test_ip(self, host_name):
        for host in self.data["boxes"]:
            if host_name == host:
                interfaces = self.data["boxes"][host_name]["interfaces"]
                for interface in interfaces:
                    if interface["type"] == "test":
                        return interface["ip-address"]
        print("error: get_test_ip not found for {}\n".format(host_name))
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

    def get_test_iface_name(self, host_name):
        for host in self.data["boxes"]:
            if host_name == host:
                interfaces = self.data["boxes"][host_name]["interfaces"]
                for interface in interfaces:
                    if interface["type"] == "test":
                        return interface["name"]
        print("error: get_test_iface_name not found for {}\n".format(host_name))
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

    def get_test_default_route(self, host_name):
        for host in self.data["boxes"]:
            if host_name == host:
                interfaces = self.data["boxes"][host_name]["interfaces"]
                for interface in interfaces:
                    if interface["type"] == "test":
                        return interface["default-route"]
        print("error: get_test_default_route not found for {}\n"
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

    def get_user(self, host_name):
        for host in self.data["boxes"]:
            if host_name == host:
                return self.data["boxes"][host_name]["user"]
        print("error: get_user not found for {}\n".format(host_name))
        sys.exit(1)


class AppletExecuter():

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
        parser.add_option( "-v", "--verbose", dest="verbose", default=False,
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
            self.p.err("Applet ({}) not available, call list\n".format(self.applet_name))
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
        # if the status is false the campaing must be
        # stopped, if true everything is fine!
        self.p.msg("{}\n".format(self.applet_args),
                   level=Printer.VERBOSE)
        status = self.applet.main(xchange, Conf(), self.applet_args)
        if status == True:
            return True
        elif status == False:
            return False
        else:
            print("Applet defect: MUST return True or False")
            return False


class AppletLister():

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


class CampaignExecuter():

    current_campaign_applet = 0
    campaign_length = int()
    OPCODE_CMD_EXEC = 1
    OPCODE_CMD_SLEEP = 2
    OPCODE_CMD_PRINT = 3

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
        parser.add_option( "-v", "--verbose", dest="verbose", default=False,
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
        if self.current_campaign_applet > 0:
            sys.stdout.write("[{}/{}] {}\n".format(self.current_campaign_applet,
                                                   self.campaign_length,
                                                   applet_name))
        self.current_campaign_applet += 1
        app_executer = AppletExecuter(external_controlled=True,
                                      verbose=self.verbose)
        app_executer.set_applet_data(applet_name, applet_args)
        app_status = app_executer.run()
        if not app_status:
            print("Applet returned negative return code, stopping campaign now")
            sys.exit(1)

    def read_campaign_file(self, path):
        data = list()
        with open(path, "rt") as fd:
            while True:
                line = fd.readline()
                if not line:
                    break
                line = line.strip()
                if not line:
                    # ignore lines with only with spaces
                    continue
                if line.startswith("#"):
                    # ignore comment lines
                    continue
                data.append(line)
        return data

    def transform_exec_statement(self, chunks, ret):
        d = dict()
        if not len(chunks) > 0:
            # need a second value
            return
        d['cmd'] = CampaignExecuter.OPCODE_CMD_EXEC
        d['name'] = chunks[0]
        d['args'] = chunks[1:]
        ret.append(d)

    def transform_sleep_statement(self, chunks, ret):
        d = dict()
        if not len(chunks) > 0:
            # need a second value
            return
        d['cmd'] = CampaignExecuter.OPCODE_CMD_SLEEP
        d['time'] = chunks[0]
        ret.append(d)

    def transform_print_statement(self, chunks, ret):
        d = dict()
        if not len(chunks) > 0:
            # need a second value
            return
        d['cmd'] = CampaignExecuter.OPCODE_CMD_PRINT
        d['msg'] = chunks[:]
        ret.append(d)

    def transform(self, content):
        data = list()
        for c in content:
            chunks = c.split()
            if len(chunks) < 1:
                print("Command ({}) not known, only exec and sleep allowed".format(c))
                return None, False
            if chunks[0] == "exec":
                self.transform_exec_statement(chunks[1:], data)
            elif chunks[0] == "sleep":
                self.transform_sleep_statement(chunks[1:], data)
            elif chunks[0] == "print":
                self.transform_print_statement(chunks[1:], data)
            else:
                self.p.err("Command \"{}\" not known, only exec, sleep and "
                           "print allowed".format(chunks[0]))
                return None, False
        return data, True

    def execute_campaign(self, data):
        test_no = len(data)
        run_no = 1
        for d in data:
            ret = True
            cmd = "unknown"
            #if d['cmd'] == CampaignExecuter.OPCODE_CMD_EXEC:
            cmd = "exec {}".format(d['name'])
            self.p.msg("  [{}/{}] {}\n".format(run_no, test_no,
                                             cmd), level=Printer.STD)
            ret = self.execute_applet(d['name'] + " " + d['args'])
            # elif
            if d['cmd'] == CampaignExecuter.OPCODE_CMD_SLEEP:
                cmd = "sleep {}".format(d['time'])
                self.p.msg("  [{}/{}] {}\n".format(run_no, test_no,
                                                 cmd), level=Printer.STD)
                time.sleep(int(d['time']))
            elif d['cmd'] == CampaignExecuter.OPCODE_CMD_PRINT:
                # when we print we do not print the print
                self.p.msg("  # {}\n".format(" ".join(d['msg'])), level=Printer.STD)

            if ret == False:
                print("Applet returned negative return code, stop campaign now")
                return
            run_no += 1

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

    def parse_campaign_size(self, ffp):
        campaign_file = open(ffp)
        campaign_string = campaign_file.read()
        campaign_file.close()
        # two whitespaces for not counting comments
        amount_execs = campaign_string.count("  x.exec")
        return amount_execs

    def run(self):
        data, ok = self.parse_campaign()
        if not ok:
            sys.exit(1)
        self.p.msg("Execute Campaign \"{}\"\n".format(self.campaign_name),
                   level=Printer.STD)
        ffp = self.import_campaign_module()
        self.campaign_length = self.parse_campaign_size(ffp)
        # ssh class and ping
        xchange = Exchange()
        # printer (p.msg)
        xchange.p = self.p
        # applet name and args, creates AppletExecuter() and calls its run
        xchange.exec = self.execute_applet
        # starts the campaign run
        self.campaign.main(xchange)


class CampaignLister():

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
       "exec-applet":    [ "AppletExecuter",   "Execute applets" ],
       "list-applets":   [ "AppletLister",     "List all applets" ],
       "exec-campaign":  [ "CampaignExecuter", "Execute campaign" ],
       "list-campaigns": [ "CampaignLister",   "List all campaigns" ]
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
        sys.stdout.write("%s\n" % (__version__))

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
                if arg == cmd: return True
        return False

    def parse_global_otions(self):
        if len(sys.argv) <= 1:
            self.print_usage()
            sys.stderr.write("Available applets:\n")
            self.print_modules()
            return None

        self.binary_path = sys.argv[-1]

        # --version can be placed somewhere in the
        # command line and will evalutated always: it is
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
            sys.stderr.write("Modules \"%s\" not known, available modules are:\n" %
                             (submodule))
            self.print_modules()
            return None

        classname = NetAppletShuffler.modes[submodule][0]
        return classname


    def run(self):
        classtring = self.parse_global_otions()
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
