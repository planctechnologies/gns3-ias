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

class _authenticate(object):
    pass

class ObjectStorage(object):
    def __init__(self, username, apikey):
        self.username = username
        self.apikey = apikey


    def get_account(self):
        return self.client.get_account()

    def set_container(self, container_name):
        self.container_name = container_name

    def head_container(self):
        return self.client.head_container(self.container_name)

    def get_container(self):
        return self.client.get_container(self.container_name)

    def get_object(self, item_name):
        return self.client.get_object(self.container_name, item_name)

    def delete_object(self, item_name):
        return self.client.delete_object(self.container_name, item_name)

    def put_object(self, item_name, contents):
        return self.client.put_object(self.container_name, item_name, contents)

