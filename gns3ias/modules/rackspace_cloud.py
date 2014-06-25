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

LOG_NAME = "gns3ias"
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

        # Only look for images owned by my rackspace account
        request_url = "%s/images?status=active&owner=%s" % (
            self.region_images_public_endpoint_url,
            self.auth_response['access']['token']['tenant']['id'],
        )
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

    def share_images_by_id(self, callback, tenant_id, images):
        """
        Share the provided image IDs with the tenant ID
        """
        # prepare http request for sharing an image
        request_data = json.dumps({
            "member": tenant_id
        })
        token = self.auth_response["access"]["token"]["id"]
        log.info("Auth Token: %s" % token)
        request_headers = {
            "Content-Type": "application/json",
            "X-Auth-Token": token,
        }

        # share each image synchronously
        data = []
        for image_id, image_name in images.items():
            request_url = "%s/images/%s/members" % (self.region_images_public_endpoint_url,
                                                    image_id)

            http_request = tornado.httpclient.HTTPRequest(
                url=request_url,
                method="POST",
                headers=request_headers,
                body=request_data,
            )

            try:
                http_client = tornado.httpclient.HTTPClient()
                response = http_client.fetch(http_request)
                response_data = json.loads(response.body.decode('utf8'))
                response_data["image_name"] = image_name
                data.append(response_data)
            except tornado.httpclient.HTTPError as e:
                if e.code == 409:
                    data.append({
                        "image_name": image_name,
                        "image_id": image_id,
                        "member_id": tenant_id,
                        "status": "ALREADYREQUESTED"
                    })
                else:
                    raise
            finally:
                http_client.close()

        if callback:
            callback(json.dumps(data))
