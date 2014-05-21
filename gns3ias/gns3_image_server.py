# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 GNS3 Technologies Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# __version__ is a human-readable version number.

# __version_info__ is a four-tuple for programmatic comparison. The first
# three numbers are the components of the version number. The fourth
# is zero for an official release, positive for a development branch,
# or negative for a release candidate or beta (after the base version
# number has been incremented)

import os
import sys
import time
import getopt
import datetime
import logging
import fcntl
import glob

import tornado.ioloop
import tornado.web

SCRIPT_NAME = os.path.basename(__file__)
SCRIPT_PATH = os.path.join(os.path.dirname(os.path.abspath(
    sys.argv[0])))

APP_SOURCE_PATH = os.path.join(os.path.dirname(os.path.abspath(
    sys.argv[0])),
    '..')

EXTRA_LIB = "%s/lib" % (SCRIPT_PATH)

sys.path.append(APP_SOURCE_PATH)
sys.path.append(EXTRA_LIB)

# usage method
def usage():
    usage = """
USAGE: %s

Options:

  -d, --debug         Enable debugging
  -v, --verbose       Enable verbose logging
  -h, --help          Display this menu :)

  --apikey <api_key>  Rackspace API key           
  --auth_version
  --user
  --key
  --tenant_name


""" % (SCRIPT_NAME)
    return usage

# Parse cmd line options
def parse_cmd_line(argv):
    """
    Parse command line arguments

    argv: Pass in cmd line arguments
    config: Global Config object to update with the configuration
    """

    short_args = "dvh"
    long_args = ("debug",
                    "verbose",
                    "help",
                    "batch_size=",
                    "tmp_dir=",
                    "container_name=",
                    "authurl=",
                    "auth_version=",
                    "user=",
                    "key=",
                    "tenant_name=",
                    )
    try:
        opts, extra_opts = getopt.getopt(argv[1:], short_args, long_args)
    except getopt.GetoptError, e:
        print "Unrecognized command line option or missing required argument: %s" %(e)
        print usage()
        sys.exit(253)

    cmd_line_option_list = {}
    cmd_line_option_list["batch_size"] = 100
    cmd_line_option_list["debug"] = False
    cmd_line_option_list["verbose"] = False
    cmd_line_option_list["tmp_dir"] = None
    cmd_line_option_list["container_name"] = None
    cmd_line_option_list["authurl"] = None
    cmd_line_option_list["auth_version"] = None
    cmd_line_option_list["user"] = None
    cmd_line_option_list["key"] = None
    cmd_line_option_list["tenant_name"] = None

    for opt, val in opts:
        if (opt in ("-h", "--help")):
            print usage()
            sys.exit(0)
        elif (opt in ("-d", "--debug")):
            cmd_line_option_list["debug"] = True
        elif (opt in ("-v", "--verbose")):
            cmd_line_option_list["verbose"] = True
        elif (opt in ("--batch_size",)):
            cmd_line_option_list["batch_size"] = val
        elif (opt in ("--tmp_dir")):
            cmd_line_option_list["tmp_dir"] = val
        elif (opt in ("--container_name")):
            cmd_line_option_list["container_name"] = val
        elif (opt in ("--authurl")):
            cmd_line_option_list["authurl"] = val
        elif (opt in ("--auth_version")):
            cmd_line_option_list["auth_version"] = val
        elif (opt in ("--user")):
            cmd_line_option_list["user"] = val
        elif (opt in ("--key")):
            cmd_line_option_list["key"] = val
        elif (opt in ("--tenant_name")):
            cmd_line_option_list["tenant_name"] = val

    return cmd_line_option_list

def set_logging(cmd_options):
    #Setup logging
    log = logging.getLogger("%s" % (SCRIPT_NAME))
    log_level = logging.INFO
    log_level_console = logging.WARNING

    if cmd_options['verbose'] == True:
        log_level_console = logging.INFO

    if cmd_options['debug'] == True:
        log_level_console = logging.DEBUG
        log_level = logging.DEBUG

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    console_log = logging.StreamHandler()
    console_log.setLevel(log_level_console)
    console_log.setFormatter(formatter)

    log.setLevel(log_level)
    log.addHandler(console_log)

    return log


def main():

    options = parse_cmd_line(sys.argv)
    log = set_logging(options)
    
    pid_file = "%s/%s.pid" % (SCRIPT_PATH, SCRIPT_NAME)
    fp = open(pid_file, 'w')
    try:
        fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        log.critical("Another instance is already running!!!!!")
        sys.exit(1)

    fp.write("%s"%(os.getpid()))
    fp.flush()

    log.debug("Using settings:")
    for key, value in options.iteritems():
        log.debug("%s : %s" % (key, value))
    

    #Make sure this gets called at the end, the lock is released on
    #process exit. However if the pid file has a PID in it, it 
    #means an unclean shutdown occurred.
    fp.truncate(0)
    fp.close()


if (__name__ == '__main__'):
    result = main()
    sys.exit(result)

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")

application = tornado.web.Application([
    (r"/", MainHandler),
])

if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
