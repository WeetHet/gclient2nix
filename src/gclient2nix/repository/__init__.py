import json
import subprocess
import os
import shlex
import hashlib
from logging import Logger
import tempfile

from gclient2nix.depot_tools import gclient_eval

from gclient2nix.repository.utils import (
    temporary_cache_dir,
    cache,
    cache_key,
    cache_extra_data,
    repo_from_dep,
)

logger = Logger(__name__)

BUILD_DIRECTORY = tempfile.mkdtemp()


class Repository:
    def __init__(self):
        self.deps = {}
        self.url = ""
        self.rev = ""

    def get_file(self, filepath):
        key = cache_key(self.flatten_repr())
        if "store_path" not in cache_extra_data[key]:
            logger.debug("Repo.get_file: calling Repo.prefetch to set store_path")
            self.prefetch()
        if "store_path" not in cache_extra_data[key]:
            raise RuntimeError("Repo.prefetch failed to set store_path")
        store_path = cache_extra_data[key]["store_path"]
        if not os.path.exists(store_path):
            raise RuntimeError(f"missing store_path {store_path}")
        if os.path.isdir(store_path):
            with open(store_path + "/" + filepath) as f:
                return f.read()
        cmd = f"tar -t -f {store_path} | head -n1"
        logger.debug(cmd)
        toplevel_path = subprocess.check_output(
            cmd, shell=True, encoding="utf8"
        ).strip()
        logger.debug("toplevel_path", repr(toplevel_path))
        if toplevel_path[-1] != "/":
            toplevel_path = ""
        cmd = [
            "bsdtar",
            "--fast-read",
            "-x",
            "-f",
            store_path,
            "--to-stdout",
            "--",
            toplevel_path + filepath,
        ]
        logger.debug(shlex.join(cmd))
        file_content = subprocess.check_output(cmd)
        logger.debug("file_content:", repr(file_content[0:100]) + "...")
        try:
            file_content = file_content.decode("utf8")
        except UnicodeDecodeError:
            pass
        return file_content

    def get_deps(self, repo_vars, path):
        logger.debug("evaluating " + json.dumps(self, default=vars))

        deps_file = self.get_file("DEPS")
        evaluated = gclient_eval.Parse(deps_file, filename="DEPS")

        repo_vars = dict(evaluated["vars"]) | repo_vars

        prefix = (
            f"{path}/"
            if (evaluated.get("use_relative_paths", False) and path != "")
            else ""
        )

        self.deps = {
            prefix + dep_name: repo_from_dep(dep)
            for dep_name, dep in evaluated["deps"].items()
            if (
                gclient_eval.EvaluateCondition(dep["condition"], repo_vars)
                if "condition" in dep
                else True
            )
            and repo_from_dep(dep) is not None
        }

        for key in evaluated.get("recursedeps", []):
            dep_path = prefix + key
            if dep_path in self.deps and dep_path != "src/third_party/squirrel.mac":
                dep = self.deps[dep_path]
                assert dep is not None
                dep.get_deps(repo_vars, dep_path)

    def prefetch(self):
        key = cache_key(self.flatten_repr())

        if key not in cache:
            cmd = ["nurl", self.url, self.rev]

            logger.debug(shlex.join(cmd))
            out = subprocess.check_output(cmd)
            cache[key] = out.decode("utf-8").strip()

            key_hash = hashlib.sha256(key.encode("utf8")).hexdigest()
            cache_file = temporary_cache_dir + "/" + key_hash
            logger.debug(f"Writing temporary cache file {cache_file}")
            with open(cache_file, "w") as f:
                json.dump({"key": key, "value": cache[key]}, f)

            if key not in cache_extra_data:
                cache_extra_data[key] = {}

        if key not in cache_extra_data:
            cache_extra_data[key] = {}

        if "store_path" not in cache_extra_data[key]:
            logger.debug("Getting store path")
            nix_expr = f"with import <nixpkgs> {{}}; {cache[key]}"
            cmd = ["nix-build", "--no-out-link", "-E", nix_expr]
            logger.debug(shlex.join(cmd))

            out = subprocess.check_output(cmd, cwd=BUILD_DIRECTORY)
            store_path = out.decode("utf-8").strip()
            logger.debug("Store path: ", store_path)
            cache_extra_data[key]["store_path"] = store_path

        self.expr = cache[key]

    def prefetch_all(self):
        logger.debug(self.url, self.rev)
        self.prefetch()
        for [_, dep] in self.deps.items():
            assert dep is not None
            dep.prefetch_all()

    def flatten_repr(self) -> dict[str, str]:
        return {"url": self.url, "rev": self.rev}

    def flatten(self, path) -> dict[str, str]:
        out = {path: self.expr}
        for dep_path, dep in self.deps.items():
            assert dep is not None
            out |= dep.flatten(dep_path)
        return out
