from gclient2nix.repository import Repository


class GitRepository(Repository):
    def __init__(self, url, rev):
        super().__init__()
        if url.endswith(".git"):
            url = url[:-4]
        self.url = url
        self.rev = rev
