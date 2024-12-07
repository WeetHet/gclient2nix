from gclient2nix.repository import Repository
from urllib.request import urlopen


class GitHubRepository(Repository):
    def __init__(self, owner, repo, rev):
        super().__init__()
        self.args = {
            "owner": owner,
            "repo": repo,
            "rev": rev,
        }

        self.url = f"https://github.com/{owner}/{repo}"
        self.rev = rev

    def get_file(self, filepath):
        return (
            urlopen(
                f"https://raw.githubusercontent.com/{self.args['owner']}/{self.args['repo']}/{self.args['rev']}/{filepath}"
            )
            .read()
            .decode("utf-8")
        )
