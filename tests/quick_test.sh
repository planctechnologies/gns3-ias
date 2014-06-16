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
