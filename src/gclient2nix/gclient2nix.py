from logging import Logger
import os
import re
import subprocess
import json
from datetime import datetime
import click

from gclient2nix.repository import Repository
from gclient2nix.repository.utils import load_temporary_cache, temporary_cache_dir
from gclient2nix.transform_sources import transform_sources


def get_gn_source(repo):
    gn_pattern = r"'gn_version': 'git_revision:([0-9a-f]{40})'"
    gn_commit = re.search(gn_pattern, repo.get_file("DEPS")).group(1)  # type: ignore
    gn = subprocess.check_output(
        [
            "nix-prefetch-git",
            "--quiet",
            "https://gn.googlesource.com/gn",
            "--rev",
            gn_commit,
        ]
    )
    gn = json.loads(gn)
    return {
        "gn": {
            "version": datetime.fromisoformat(gn["date"]).date().isoformat(),
            "url": gn["url"],
            "rev": gn["rev"],
            "sha256": gn["sha256"],
        }
    }


@click.command()
@click.argument("url")
@click.argument("rev")
@click.option("--main-source-path", default="")
@click.option("-o", "--output-file", default="sources.nix")
@click.option(
    "-n", "--name", default="combined-sources", help="resulting derivation name"
)
def main(url: str, rev: str, main_source_path: str, output_file: str, name: str):
    """Convert Google build tools expressions to json source list"""

    logger = Logger(__name__)

    os.makedirs(temporary_cache_dir, exist_ok=True)
    load_temporary_cache()

    repo_vars = {
        f"checkout_{platform}": platform in ["linux", "mac"]
        for platform in ["ios", "chromeos", "android", "mac", "win", "linux"]
    }

    main_repo = Repository()
    main_repo.url = url
    main_repo.rev = rev

    logger.info("Fetching the main source")
    main_repo.prefetch()

    logger.info("parsing sources of dependencies")
    logger.debug("args.main_source_path:", repr(main_source_path))
    repo_vars = {
        f"checkout_{platform}": platform in ["linux", "mac"]
        for platform in ["ios", "chromeos", "android", "mac", "win", "linux"]
    }
    main_repo.get_deps(repo_vars, main_source_path)

    logger.debug("fetching sources of dependencies")
    main_repo.prefetch_all()

    tree = main_repo.flatten(main_source_path)

    logger.debug(f"writing output file: {output_file}")
    with open(output_file, "w") as f:
        f.write(transform_sources(name, tree))
    subprocess.check_output(["nixfmt", output_file])
