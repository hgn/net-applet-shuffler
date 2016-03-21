# do nothing, just returns true
# can be used for internal nas tests

def main(x, conf, args):
    x.p.msg("do nothing\n", level=x.p.VERBOSE)
    return True
