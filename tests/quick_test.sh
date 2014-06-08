#!/bin/bash

base_url="http://127.0.0.1:8888/images/grant_access"

echo $base_url
curl $base_url
echo -e "\n\n"

test_url=${base_url}?user_id=123456789
echo $test_url
curl $test_url
echo -e "\n\n"

test_url=${base_url}?user_id=123456789\&gns3_version=3.0
echo $test_url
curl $test_url
echo -e "\n\n"

test_url=${base_url}?user_id=907389\&gns3_version=3.0\&user_region=IAD
echo $test_url
curl $test_url
echo -e "\n\n"

#curl http://127.0.0.1:8888/images?user_id=123456789
#curl http://127.0.0.1:8888/images?user_id=123456789&gns3_version=3.0
#curl http://127.0.0.1:8888/images?user_id=123456789&gns3_version=3.0

#curl http://127.0.0.1:8888/images?user_id=123456789&gns3_version=3.0


#curl -s https://identity.api.rackspacecloud.com/v2.0/tokens -X 'POST' \
#     -d '{"auth":{"passwordCredentials":{"username":"yourUserName", "password":"yourPassword"}}}' \
#     -H "Content-Type: application/json" | python -m json.tool

#curl -s https://identity.api.rackspacecloud.com/v2.0/tokens -X 'POST' \
#     -d '{"auth":{"RAX-KSKEY:apiKeyCredentials":{"username":"galemichael", "apiKey":"9929e90e695584bfa545cdbe6e9cb43a"}}}' \
#     -H "Content-Type: application/json" | python -m json.tool



################ CURL 
# POST / HTTP/1.1
# User-Agent: curl/7.35.0
# Host: 127.0.0.1:8888
# Accept: */*
# Content-Type: application/json
# Content-Length: 112

# {"auth":{"RAX-KSKEY:apiKeyCredentials":{"username":"galemichael", "apiKey":"9929e90e695584bfa545cdbe6e9cb43a"}}}HTTP/1.1 405 Method Not Allowed
# Date: Mon, 26 May 2014 05:00:59 GMT
# Server: TornadoServer/3.2.1
# Content-Type: text/html; charset=UTF-8
# Content-Length: 87

# <html><title>405: Method Not Allowed</title><body>405: Method Not Allowed</body></html>

################# PYCURL
# POST /tokens HTTP/1.1
# User-Agent: Mozilla/5.0 (compatible; pycurl)
# Host: 127.0.0.1:8888
# Accept: */*
# Accept-Encoding: gzip,deflate
# Content-Type: application/json
# Content-Length: 116

# {"auth": {"RAX-KSKEY:apiKeyCredentials": {"apiKey": "9929e90e695584bfa545cdbe6e9cb43a", "username": "galemichael"}}}HTTP/1.1 404 Not Found
# Server: TornadoServer/3.2.1
# Date: Mon, 26 May 2014 05:40:01 GMT
# Content-Type: text/html; charset=UTF-8
# Content-Length: 69

# <html><title>404: Not Found</title><body>404: Not Found</body></html>