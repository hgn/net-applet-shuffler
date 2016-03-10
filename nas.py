#!/usr/bin/python3
#
# Email: Hagen Paul Pfeifer <hagen@jauu.net>


import sys
import os
import optparse
import subprocess
import pprint
import re
import ctypes
import math
import time
import importlib.util
import json
import subprocess


pp = pprint.PrettyPrinter(indent=4)

__programm__ = "net-applet-shuffler"
__version__  = "1"


class Printer:

    def __init__(self, verbose=False):
        self.verbose = verbose

    def set_verbose(self):
        self.verbose = True

    def err(self, msg):
        sys.stderr.write(msg)

    def verbose(self, msg):
        if not self.verbose:
            return
        sys.stderr.write(msg)

    def msg(self, msg):
        return sys.stdout.write(msg) - 1

    def line(self, length, char='-'):
        sys.stdout.write(char * length + "\n")

    def msg_underline(self, msg, pre_news=0, post_news=0):
        str_len = len(msg)
        if pre_news:
            self.msg("\n" * pre_news)
        self.msg(msg)
        self.msg("\n" + '=' * str_len)
        if post_news:
            self.msg("\n" * post_news)

class Ssh():

    def __init__(self):
        pass

    def exec(self, ip, user, cmd):
        full = "ssh {}@{} sudo {}".format(user, ip, cmd)
        p = subprocess.Popen(full.split(), stdout=subprocess.PIPE)
        stderr, stdout = p.communicate()
        return stdout, stderr, p.returncode


class Exchange():

    def __init__(self):
        self.ssh = Ssh()

    def ping(self, host):
        cmd = "ping -c 1 {} 1>/dev/null 2>&1 ".format(host)
        response = os.system(cmd)
        if response == 0:
            return True
        return False


class AppletExecuter():

    def __init__(self):
        self.p = Printer()
        self.parse_local_options()
        self.import_applet_module()
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

    def import_applet_module(self):
        ffp, ok = self.applet_path(self.applet_name)
        if not ok:
            self.p.err("Applet ({}) not avaiable, call list\n".format(self.applet_name))
            sys.exit(1)

        spec = importlib.util.spec_from_file_location("applet", ffp)
        self.applet = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.applet)

    def run(self):
        xchange = Exchange()
        xchange.p = self.p
		# the status is used later for campaigns:
		# if the status is false the campaing must be
		# stopped, if true everything is fine!
        status = self.applet.main(xchange, self.conf, self.applet_args)
        if status == True:
            pass
        elif status == False:
            sys.exit(1)
        else:
            print("applet defect: MUST return True or False")
            sys.exit(1)


class AppletLister():

    def __init__(self):
        self.p = Printer()

    def subdirs(self, d):
        return [name for name in os.listdir(d) if os.path.isdir(os.path.join(d, name))]

    def run(self):
        hp = os.path.dirname(os.path.realpath(__file__))
        fp = os.path.join(hp, "applets")
        dirs = self.subdirs(fp)
        sys.stdout.write("Available applets:\n")
        for d in dirs:
            sys.stdout.write("  {}\n".format(d))


class CampaignExecuter():

    def __init__(self):
        self.p = Printer()
        self.parse_local_options()

    def campaign_path(self, name):
        hp = os.path.dirname(os.path.realpath(__file__))
        fp = os.path.join(hp, "campaign", name)
        if not os.path.exists(fp):
            return None, False
        ffp = os.path.join(fp, "run.cmd")
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

    def check_campaign(self):
        """
        parse every line, ignore comment lines (starting with #)
        and call AppletExecuter.validate_path() for each exec applet
        to verify that the applet is at least available.
        Note that only lines with prefix "exec" must be validated
        """
        pass

    def execute_campaign(self):
        pass

    def run(self):
        ok = self.check_campaign()
        if not ok:
            sys.exit(1)
        self.execute_campaign()


class NetAppletShuffler:

    modes = {
       "exec-applet":    [ "AppletExecuter",   "Execute applets" ],
       "list-applets":   [ "AppletLister",     "List all applets" ],
       "exec-campaign":  [ "CampaignExecuter", "Execute campaign" ],
       "list-campaogns": [ "CampaignLister",   "List all campaigns" ]
            }

    def __init__(self):
        pass

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

        classinstance = globals()[classtring]()
        classinstance.run()
        return 0


if __name__ == "__main__":
    try:
        mca = NetAppletShuffler()
        sys.exit(mca.run())
    except KeyboardInterrupt:
        sys.stderr.write("SIGINT received, exiting\n")
