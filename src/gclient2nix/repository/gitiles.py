import base64

from gclient2nix.repository import Repository
from urllib.request import urlopen


class GitilesRepository(Repository):
    def __init__(self, url, rev):
        super().__init__()
        if url.endswith(".git"):
            url = url[:-4]

        self.url = url
        self.rev = rev

    def get_file(self, filepath):
        return base64.b64decode(
            urlopen(f"{self.url}/+/{self.rev}/{filepath}?format=TEXT").read()
        ).decode("utf-8")
