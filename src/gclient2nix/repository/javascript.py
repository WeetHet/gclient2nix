import subprocess
import tempfile
import sys

from gclient2nix.repository.utils import cache, cache_key


def get_yarn_hash(repo, yarn_lock_path="yarn.lock"):
    key = "yarn-" + cache_key(repo.flatten_repr())
    if key not in cache:
        logger.debug("prefetch-yarn-deps")
        with tempfile.TemporaryDirectory() as tmp_dir:
            with open(tmp_dir + "/yarn.lock", "w") as f:
                f.write(repo.get_file(yarn_lock_path))
            cache[key] = (
                subprocess.check_output(["prefetch-yarn-deps", tmp_dir + "/yarn.lock"])
                .decode("utf-8")
                .strip()
            )
    return cache[key]


def get_npm_hash(repo, package_lock_path="package-lock.json"):
    key = "npm-" + cache_key(repo.flatten_repr())
    if key not in cache:
        logger.debug("prefetch-npm-deps")
        with tempfile.TemporaryDirectory() as tmp_dir:
            with open(tmp_dir + "/package-lock.json", "w") as f:
                f.write(repo.get_file(package_lock_path))
            cache[key] = (
                subprocess.check_output(
                    ["prefetch-npm-deps", tmp_dir + "/package-lock.json"]
                )
                .decode("utf-8")
                .strip()
            )
    return cache[key]
