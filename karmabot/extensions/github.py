# Copyright the Karmabot authors and contributors.
# All rights reserved.  See AUTHORS.
#
# This file is part of 'karmabot' and is distributed under the BSD license.
# See LICENSE for more details.
import urllib

import json

from karmabot.core.register import facet_registry
from karmabot.core.facets import Facet
from karmabot.core.commands import thing, CommandSet
from karmabot.core.utils import Cache


@facet_registry.register
class GitHubFacet(Facet):
    name = "github"
    commands = thing.add_child(CommandSet(name))

    def __init__(self, thing):
        super(self, Facet).__init__(self, thing)
        self.get_info = Cache(self._get_info, expire_seconds=10 * 60)

    @classmethod
    def does_attach(cls, thing):
        return False

    @commands.add(u"forget that {thing} is on github",
                  help=u"unset {thing}'s github username",
                  exclusive=True)
    def unset_github_username(self, thing, context):
        del self.data
        self.thing.remove_facet(self)

    @commands.add(u"{thing} has github username {username}",
                  u"set {thing}'s github username to {username}")
    def set_github_username(self, thing, username, context):
        self.username = username

    @property
    def username(self):
        return self.data.get("username", self.thing.name)

    @username.setter
    def set_username(self, value):
        if "username" not in self.data or value != self.data["username"]:
            self.data["username"] = value
            self.get_info.reset()

    def _get_info(self):
        about_url = "http://github.com/{0}.json"
        about = urllib.urlopen(about_url.format(self.username))
        return json.load(about)

    @commands.add(u"{thing} commits",
                  u"show the last 3 commits by {thing}")
    def get_github_commits(self, thing, context):
        info = self.get_info()
        pushes = filter(lambda x: x["type"] == "PushEvent", info)
        lines = []
        for push in pushes[:3]:
            lines.append(u"\"{last_commit_msg}\" -- {url}".format(
                    url=push["repository"]["url"],
                    last_commit_msg=push["payload"]["shas"][0][2]))
        context.reply("\n".join(lines))

    def present(self, context):
            github = self.thing.facets["github"]
            text = u"http://github.com/{0}".format(github.username)
            return text


@thing.add(format=u"{thing} is on github",
           help_str=u"link {thing}'s github account to their user",
           exclusive=True)
def set_githubber(thing, context):
    thing.add_facet(GitHubFacet)
