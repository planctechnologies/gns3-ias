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
import json
import tornado.ioloop
import tornado.httpclient
import urllib.request
import urllib.parse
from dateutil.parser import *
from dateutil.tz import *
from datetime import *
import logging
from functools import partial

LOG_NAME = "gns3_image_server"
log = logging.getLogger("%s" % (LOG_NAME))

class Rackspace(object):
    def __init__(self, callback, username, apikey, auth_cache=None, set_auth_cache=None):
        self.username = username
        self.apikey = apikey
        self.auth_response = auth_cache
        self.region_images_public_endpoint_url = None
        self.set_auth_cache = set_auth_cache

        #Because of the number of callbacks and async style, if a request fails
        #we have no way of knowning triggered the last request, so we need
        #to track that info.
        self.last_request_params = None

        if self.auth_response is None:
            self.get_token(callback)
        else:
            io_loop = tornado.ioloop.IOLoop.instance()
            io_loop.add_callback(callback)

    def _build_http_request(self, callback, request_url, request_data=None):

        self.last_request_params = [callback, request_url, request_data]

        request_method = "GET"
        request_headers = {"Content-Type" : "application/json"}

        if self.auth_response:
            token = self.auth_response["access"]["token"]["id"]
            request_headers["X-Auth-Token"] = token
            log.info("Auth Token: %s" % (token))

        if request_data:
            request_method = "POST"        

        http_request = tornado.httpclient.HTTPRequest(
                url = request_url,
                method = request_method,
                headers = request_headers,
                body = request_data,
            )

        tornado.httpclient.AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")
        http_client = tornado.httpclient.AsyncHTTPClient()
        http_client.fetch(http_request, callback)

    def _repeat_last_http_request(self):
        self._build_http_request(*self.last_request_params)

    def _check_authentication(self,response):
        if response.error:
            if response.code == 401:
                self.get_token(self._repeat_last_http_request)
            else:
                response.rethrow()


    def get_token(self, callback=None):
        log.info("Requesting auth token")
        self.auth_response = None
        self._get_token_callback = callback
        request_url = "https://identity.api.rackspacecloud.com/v2.0/tokens"
        request_data = json.dumps({
            "auth": {
                    "RAX-KSKEY:apiKeyCredentials": {
                        "username":"%s" % (self.username), 
                        "apiKey":"%s" % (self.apikey),
                        }
                    }
            })

        self._build_http_request(self._got_token, request_url, request_data)

    def _got_token(self, response):

        response.rethrow()
        data = json.loads(response.body.decode('utf8'))
        self.set_auth_cache(data)
        self.auth_response = data

        if self._get_token_callback:
            self._get_token_callback()

    def get_gns3_images(self, callback, region):
        """
        Return a list of images from Rackspace
        """

        self._get_gns3_images_callback = callback

        for serviceCatalog in self.auth_response["access"]["serviceCatalog"]:
            if serviceCatalog["type"] == "image":
                for endpoint in serviceCatalog["endpoints"]:
                    if endpoint["region"] == region:
                        self.region_images_public_endpoint_url = endpoint["publicURL"]
                        break
                break

        request_url = "%s/images?status=active" % (self.region_images_public_endpoint_url)
        self._build_http_request(self._got_gns3_images, request_url)

    def _got_gns3_images(self, response):
        self._check_authentication(response)
        data = json.loads(response.body.decode('utf8'))

        image_list = []
        for image in data["images"]:
            image_list.append(
                    {
                        "id" : image["id"],
                        "name" : image["name"],
                        "status" : image["status"],
                        "visibility" : image["visibility"], 
                    }
                )       

        if self._get_gns3_images_callback:
            self._get_gns3_images_callback(image_list)


    def share_image_by_id(self, callback, tenant_id, image_id):
        """
        Share the provided image ID with the tenant ID
        """
        self._share_image_by_id_callback = callback
        self.tenant_id = tenant_id
        self.image_id = image_id

        request_data = json.dumps({
            "member": self.tenant_id
            })

        request_url = "%s/images/%s/members" % (self.region_images_public_endpoint_url, 
            self.image_id)
        self._build_http_request(self._got_share_image_by_id, request_url, request_data)

    def _got_share_image_by_id(self, response):
        if response.code == 409:

            data = { "image_id": self.image_id, 
                "member_id": self.tenant_id, 
                "status": "ALREADYREQUESTED"
                }
        else:
            self._check_authentication(response)
            data = json.loads(response.body.decode('utf8'))

        if self._share_image_by_id_callback:
            self._share_image_by_id_callback(data)