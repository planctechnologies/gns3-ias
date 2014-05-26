import json
import tornado.httpclient
import urllib.request
import urllib.parse
from dateutil.parser import *
from dateutil.tz import *
from datetime import *


class Rackspace(object):
    def __init__(self, username, apikey):
        self.username = username
        self.apikey = apikey
        self.token = None
        self.token_expire_date = None
        self.auth_response = None

    def _build_http_request(self, callback, request_url, request_data=None):
        http_request = tornado.httpclient.HTTPRequest(
                url = request_url,
                method = "POST",
                headers = {'Content-Type':'application/json'},
                body = request_data,
            )

        tornado.httpclient.AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")
        http_client = tornado.httpclient.AsyncHTTPClient()
        http_client.fetch(http_request, callback)

    def _get_token(self, callback=None):
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
        data = json.loads(response.body)
        self.token = data["access"]["token"]["id"]
        self.token_expire_date = parse(data["access"]["token"]["expires"])
        self.auth_response = data

        if self._get_token_callback:
            self._get_token_callback()

    def get_gns3_images(self, region, callback):
        """
        Return a list of images from Rackspace
        """

        self._get_gns3_images_callback = callback

        for serviceCatalog in self.auth_response["access"]["serviceCatalog"]:
            if serviceCatalog["type"] == "image":
                for endpoint in serviceCatalog["endpoints"]:
                    if endpoint["region"] == region:
                        request_url = endpoint["publicURL"]
                        break
                break

        request_url = "%s?status=active" % (request_url)
        self._build_http_request(self._got_gns3_images, request_url)

    def _got_gns3_images(self, data):
        response.rethrow()
        data = json.loads(response.body)
        print(data)

        self._got_gns3_images(data)


    def share_image_by_id(self, tenant_id, image_id):
        """
        Share the provided image ID with the tenant ID
        """
        pass

    def share_image_by_name(self, tenant_id, image_name):
        """
        Share the provided image name with the tenant ID
        """
        pass