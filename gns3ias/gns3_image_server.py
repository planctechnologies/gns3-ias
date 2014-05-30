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

"""
Shares Rackspace GNS3 server images with other Rackspace customers. In theory 
any cloud provider could be used.
"""

import os
import sys
import time
import getopt
import datetime
import logging
import fcntl
import glob
import json
import signal

import tornado.ioloop
import tornado.web

SCRIPT_NAME = os.path.basename(__file__)
SCRIPT_PATH = os.path.join(os.path.dirname(os.path.abspath(
    sys.argv[0])))

APP_SOURCE_PATH = os.path.join(os.path.dirname(os.path.abspath(
    sys.argv[0])),
    '..')

EXTRA_LIB = "%s/modules" % (SCRIPT_PATH)

sys.path.append(APP_SOURCE_PATH)
sys.path.append(EXTRA_LIB)

import rackspace_cloud

TOTAL_REQUESTS = 0
TOTAL_REQUESTS_ERRORS = 0
options = {}


usage = """
USAGE: %s

Options:

  -d, --debug         Enable debugging
  -v, --verbose       Enable verbose logging
  -h, --help          Display this menu :)

  --cloud_api_key <api_key>  Rackspace API key           
  --cloud_user_name
  
  -p, --port          Server port to run on

  --image_id          Override the image id, this is useful for testing.

  -k                  Kill previous instance running in background

""" % (SCRIPT_NAME)

# Parse cmd line options
def parse_cmd_line(argv):
    """
    Parse command line arguments

    argv: Pass in cmd line arguments
    """

    short_args = "dvhp:"
    long_args = ("debug",
                    "verbose",
                    "help",
                    "cloud_user_name=",
                    "cloud_api_key=",
                    "port=",
                    "image_id=",
                    )
    try:
        opts, extra_opts = getopt.getopt(argv[1:], short_args, long_args)
    except getopt.GetoptError as e:
        print("Unrecognized command line option or missing required argument: %s" %(e))
        print(usage)
        sys.exit(2)

    cmd_line_option_list = {}
    cmd_line_option_list["debug"] = False
    cmd_line_option_list["verbose"] = False
    cmd_line_option_list["cloud_user_name"] = None
    cmd_line_option_list["cloud_api_key"] = None
    cmd_line_option_list["port"] = 8888
    cmd_line_option_list["image_id"] = None
    cmd_line_option_list["shutdown"] = False

    get_gns3secrets(cmd_line_option_list)

    for opt, val in opts:
        if (opt in ("-h", "--help")):
            print(usage)
            sys.exit(0)
        elif (opt in ("-d", "--debug")):
            cmd_line_option_list["debug"] = True
        elif (opt in ("-v", "--verbose")):
            cmd_line_option_list["verbose"] = True
        elif (opt in ("--cloud_user_name")):
            cmd_line_option_list["cloud_user_name"] = val
        elif (opt in ("--cloud_api_key")):
            cmd_line_option_list["cloud_api_key"] = val
        elif (opt in ("-p", "--port")):
            cmd_line_option_list["port"] = val
        elif (opt in ("--image_id")):
            cmd_line_option_list["image_id"] = val
        elif (opt in ("-k")):
            cmd_line_option_list["shutdown"] = True

    if cmd_line_option_list["cloud_user_name"] is None:
        print("You need to specify a username!!!!")
        print(usage)
        sys.exit(2)

    if cmd_line_option_list["cloud_api_key"] is None:
        print("You need to specify an apikey!!!!")
        print(usage)
        sys.exit(2)

    return cmd_line_option_list

def get_gns3secrets(cmd_line_option_list):
    """
    Load cloud credentials from .gns3secrets
    """

    gns3secret_paths = [
        os.path.expanduser("~/"),
        SCRIPT_PATH,
    ]

    for gns3secret_path in gns3secret_paths:
        gns3secret_file = "%s/.gns3secrets" % (gns3secret_path)
        if os.path.isfile(gns3secret_file):
            with open(gns3secret_file, 'r') as sec_file:
                for line in sec_file:
                    try:
                        (key, value) = line.split(":")
                        if key in cmd_line_option_list:
                            cmd_line_option_list[key] = value.strip()
                    except ValueError:
                        pass



def set_logging(cmd_options):
    """
    Setup logging and format output
    """
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


def main(application):

    global options
    options = parse_cmd_line(sys.argv)
    log = set_logging(options)

    def _shutdown(signalnum, frame):
        """
        Handles the SIGINT and SIGTERM event, inside of main so it has access to
        the log vars.
        """

        log.warring("Received shutdown signal")
        tornado.ioloop.IOLoop.instance().stop()
        log.warring("IO stopped")


    pid_file = "%s/%s.pid" % (SCRIPT_PATH, SCRIPT_NAME)

    if options["shutdown"]:
        os.Kill(pid_file)

    fp = open(pid_file, 'w')
    try:
        fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        log.critical("Another instance is already running!!!!!")
        sys.exit(1)

    fp.write("%s"%(os.getpid()))
    fp.flush()

    ## Setup signal to catch Control-C / SIGINT
    ## To make sure we close all threads
    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    log.debug("Using settings:")
    for key, value in iter(sorted(options.items())):
        log.debug("%s : %s" % (key, value))
    

    application.listen(options["port"])
    tornado.ioloop.IOLoop.instance().start()

    #Make sure this gets called at the end, the lock is released on
    #process exit. However if the pid file has a PID in it, it 
    #means an unclean shutdown occurred.
    fp.truncate(0)
    fp.close()


class MainHandler(tornado.web.RequestHandler):
    starttime = datetime.datetime.now()

    def get(self):
        """
        Handlers standard GET request for this http server at the base ("/") 
        path.

        We want to return help metrics, like a service health check.
        """

        message = {
            'runtime' : "%s" % (datetime.datetime.now() - self.starttime),
            'total_requests' : TOTAL_REQUESTS,
        }

        client_json = json.dumps(message)
        client_json = client_json + "\n"

        self.write(client_json)

class ImageAccessHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        """
        Handles the api call from clients:
        exmaple_image.com/images/grant_access?user_id=1234&user_region=IAD&gns3_version=3.0

        All the params are required:
        user_id: Rackspace Tenant id
        user_region: Rackspace region
        gns3_version: Version of the server image the client wants access to.

        Everything in this class is done asynchronously

        """
        self.user_id = self.get_argument("user_id")
        self.user_region = self.get_argument("user_region")
        self.gns3_version = self.get_argument("gns3_version")

        self.rksp = rackspace_cloud.Rackspace(options['username'], options['apikey'])
        self.rksp.get_token(self._get_gns3_images)

    def _get_gns3_images(self):
        """
        Gets a list of all images in a specific region
        """
        self.rksp.get_gns3_images(self._share_image, self.user_region)

    def _share_image(self, image_list):
        """
        Gets the ID of a matching image and shares it with a tenant.

        The image ID that is shared can be overwritten with a command line
        argument (--image_id=<id>). This makes testing easier.

        gns3_<version>
        """
        for image in image_list:
            if image["name"].find(self.gns3_version):
                image_id = image["id"]
       

        if options["image_id"]:
            image_id = options["image_id"]

        self.rksp.share_image_by_id(self._send_to_client,
            self.user_id,
            image_id
        )

    def _send_to_client(self, data):
        """
        Send the ID to the client and close this connection via self.finish().

        We need to explicitly call self.finish to close the connection because
        we are using the @tornado.web.asynchronous decorator.
        """

        self.write(data)
        self.finish()



application = tornado.web.Application([
    (r"/", MainHandler),
    (r"/images/grant_access", ImageAccessHandler),
])

if __name__ == "__main__":
    result = main(application)
    sys.exit(result)


