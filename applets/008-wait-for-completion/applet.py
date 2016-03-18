
import time
import sys


def is_id_running(x, host_ip, host_user, applet_id):
    _, _, exit_code = x.ssh.exec(host_ip, host_user, "test -f "
            "/tmp/net-applet-shuffler/running_{}".format(applet_id))
    # with error code == 0: file exists -> process is running
    if exit_code == 0:
        return True

    return False


def main(x, conf, args):
    if len(args) < 1:
        x.p.msg("wrong usage: first specify the interval check time "
                "interval_time:[seconds], then 1...n host:id tuples for which "
                "to wait, e.g. [name1]:[id1] [name2]:[id2] ...\n")
        return False

    # entries dictionary
    # note: a host can have multiple ids, but an id can (should) not have
    # multiple hosts -> key = unique == id, value == host
    ent_d = dict()
    # in seconds
    interval_time = int(args[0].split(":")[1])
    # read in all host:id tuples
    # len(sys.argv) includes the program name (subtract 1 due to interval time)
    for argument_number in range(0, (len(sys.argv))):
        name_host = args[argument_number].split(":")[0]
        applet_id = args[argument_number].split(":")[1]
        if not name_host == "interval_time":
            ent_d[applet_id] = name_host

    # iter through all dict entries, and test them one in an interval
    # remove items which are not running anymore
    # when the dict is empty, all processes are finished
    while len(ent_d) > 0:
        time.sleep(interval_time)

        # dict size must not change during iteration
        # therefore use a list for entries to be deleted
        entries_marked = list()
        for applet_id in ent_d:
            host_name = ent_d[applet_id]
            host_ip = conf['boxes'][host_name]["interfaces"][0]['ip-address']
            host_user = conf['boxes'][host_name]['user']
            # mark dict entry if running is false, else do nothing
            if not is_id_running(x, host_ip, host_user, applet_id):
                entries_marked.append(applet_id)

        # remove marked entries from dict
        for entry in entries_marked:
            ent_d.pop(entry)

    return True
