import json
import re
import os
from logging import Logger

from gclient2nix.depot_tools import gclient_utils

cache = {}
cache_extra_data = {}

temporary_cache_dir = "/tmp/gclient2nix-cache"

logger = Logger(__name__)


def remove_hashes(dep):
    return {attr: dep[attr] for attr in dep if attr != "hash" and attr != "sha256"}


def cache_key(dep):
    return json.dumps(remove_hashes(dep))


def repo_from_dep(dep):
    if "url" in dep:
        url, rev = gclient_utils.SplitUrlRevision(dep["url"])

        search_object = re.search(r"https://github.com/(.+)/(.+?)(\.git)?$", url)
        if search_object:
            from gclient2nix.repository.github import GitHubRepository

            return GitHubRepository(search_object.group(1), search_object.group(2), rev)

        if re.match(r"https://.+.googlesource.com", url):
            from gclient2nix.repository.gitiles import GitilesRepository

            return GitilesRepository(url, rev)

        from gclient2nix.repository.git import GitRepository

        return GitRepository(url, rev)
    else:
        return None


def load_temporary_cache():
    for filename in os.listdir(temporary_cache_dir):
        # sha256 hexdigest has 64 chars
        if len(filename) != 64:
            continue
        cache_file_path = temporary_cache_dir + "/" + filename
        logger.debug(f"loading temporary cache file {cache_file_path}")
        with open(cache_file_path) as f:
            data = json.load(f)
            key = data["key"]
            value = data["value"]
            cache[key] = value
            logger.debug(f"loaded cache key: {repr(key)}")
            logger.debug(f"loaded cache value: {repr(value)}")
