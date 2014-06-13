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
import configparser

import tornado.ioloop
import tornado.web

SCRIPT_NAME = os.path.basename(__file__)

#Is the full path when used as an import
SCRIPT_PATH = os.path.dirname(__file__)

if not SCRIPT_PATH:
    SCRIPT_PATH = os.path.join(os.path.dirname(os.path.abspath(
        sys.argv[0])))


EXTRA_LIB = "%s/modules" % (SCRIPT_PATH)


LOG_NAME = "gns3ias"
log = None

sys.path.append(EXTRA_LIB)

import daemon
import rackspace_cloud

api_info = {
    'auth_response' : None,
    'cloud_user_name' : None,
    'cloud_api_key' : None,
    'image_id' : None,
}

stats = {
    'client_total_requests' : 0,
    'client_total_requests_ok' : 0,
    'client_last_request_time' : None,
    'app_start_time' : datetime.datetime.now(),
}

stats_n_api = {
    'stats' : stats,
    'api_info' : api_info,
}

my_daemon = None 

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
  --background        Run in background

""" % (SCRIPT_NAME)

# Parse cmd line options
def parse_cmd_line(argv):
    """
    Parse command line arguments

    argv: Pass in cmd line arguments
    """

    short_args = "dvhkp:"
    long_args = ("debug",
                    "verbose",
                    "help",
                    "cloud_user_name=",
                    "cloud_api_key=",
                    "port=",
                    "image_id=",
                    "background",
                    )
    try:
        opts, extra_opts = getopt.getopt(argv[1:], short_args, long_args)
    except getopt.GetoptError as e:
        print("Unrecognized command line option or missing required argument: %s" %(e))
        print(usage)
        sys.exit(2)

    cmd_line_option_list = {}
    cmd_line_option_list["debug"] = False
    cmd_line_option_list["verbose"] = True
    cmd_line_option_list["cloud_user_name"] = None
    cmd_line_option_list["cloud_api_key"] = None
    cmd_line_option_list["port"] = 8888
    cmd_line_option_list["image_id"] = None
    cmd_line_option_list["shutdown"] = False
    cmd_line_option_list["daemon"] = False

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
        elif (opt in ("--background")):
            cmd_line_option_list["daemon"] = True

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

    config = configparser.ConfigParser()

    for gns3secret_path in gns3secret_paths:
        gns3secret_file = "%s/.gns3secrets.conf" % (gns3secret_path)
        if os.path.isfile(gns3secret_file):
            config.read(gns3secret_file)

    for key, value in config.items("Cloud"):
        cmd_line_option_list[key] = value.strip()


def set_logging(cmd_options):
    """
    Setup logging and format output
    """
    log = logging.getLogger("%s" % (LOG_NAME))
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

    access_log = logging.getLogger("tornado.access")
    access_log.setLevel(log_level)
    access_log.addHandler(console_log)

    return log

def send_shutdown(pid_file):
    with open(pid_file, 'r') as pidf:
        pid = int(pidf.readline().strip())
        pidf.close()


    os.kill(pid, 15)

def main():

    application = tornado.web.Application([
        (r"/", MainHandler, dict(stats=stats)),
        (r"/images/grant_access", ImageAccessHandler, stats_n_api),
    ])

    global log
    global my_daemon
    options = parse_cmd_line(sys.argv)
    log = set_logging(options)   

    api_info['cloud_user_name'] = options['cloud_user_name']
    api_info['cloud_api_key'] = options['cloud_api_key']
    api_info['image_id'] = options['image_id']

    def _shutdown(signalnum=None, frame=None):
        """
        Handles the SIGINT and SIGTERM event, inside of main so it has access to
        the log vars.
        """

        log.warning("Received shutdown signal")
        tornado.ioloop.IOLoop.instance().stop()
        log.warning("IO stopped")
        

    pid_file = "%s/%s.pid" % (SCRIPT_PATH, SCRIPT_NAME)

    if options["shutdown"]:
        send_shutdown(pid_file)
        sys.exit(0)

    if options["daemon"]:
        print("Starting in background ...\n")
        my_daemon = MyDaemon(pid_file, options)

    # Setup signal to catch Control-C / SIGINT and SIGTERM
    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    log.debug("Using settings:")
    for key, value in iter(sorted(options.items())):
        log.debug("%s : %s" % (key, value))
    
    log.warning("Starting ...")

    if my_daemon:
        my_daemon.start()
    else:
        application.listen(options["port"])
        tornado.ioloop.IOLoop.instance().start()


class MyDaemon(daemon.daemon):
    def run(self):
        application.listen(self.options["port"])
        tornado.ioloop.IOLoop.instance().start()

class MainHandler(tornado.web.RequestHandler):
    def initialize(self, stats):
        self.stats = stats

    def get(self):
        """
        Handlers standard GET request for this http server at the base ("/") 
        path.

        We want to return help metrics, like a service health check.
        """

        message = {
            'runtime' : "%s" % (datetime.datetime.now() - self.stats['app_start_time']),
            'total_requests' : self.stats['client_total_requests'],
            'total_requests_ok' : self.stats['client_total_requests_ok'],
            'last_request_time' : self.stats['client_last_request_time'],
        }

        client_json = json.dumps(message)
        client_json = client_json + "\n"

        self.write(client_json)

class ImageAccessHandler(tornado.web.RequestHandler):
    def initialize(self, stats, api_info):
        self.stats = stats
        self.api_info = api_info

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
        self.stats['client_total_requests']+=1
        self.stats['client_last_request_time'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        
        self.user_id = self.get_argument("user_id")
        self.user_region = self.get_argument("user_region")
        self.gns3_version = self.get_argument("gns3_version")

        self.rksp = rackspace_cloud.Rackspace(
                self._get_gns3_images,
                self.api_info['cloud_user_name'], 
                self.api_info['cloud_api_key'],
                self.api_info['auth_response'],
                self._set_auth_cache,
            )

    def _set_auth_cache(self, data):
        self.api_info['auth_response'] = data
        log.info("Cache updated")

    def _print_images(self, image_list):
        for image in image_list:
            print(image)

        self.write("Thanks\n")
        self.finish()

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
       

        if self.api_info["image_id"]:
            image_id = self.api_info["image_id"]

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
        self.stats['client_total_requests_ok']+=1
        self.finish()


if __name__ == "__main__":
    result = main()
    sys.exit(result)


