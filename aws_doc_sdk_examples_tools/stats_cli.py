import sys
import tempfile
import yaml

from colorama import Fore, Style, init
from io import StringIO
from pathlib import Path

from .shgit import Sh
from .stats import main as stats


# Initialize colorama for Windows compatibility (does nothing on Linux/macOS)
init(autoreset=True)


class Capturing(list):
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self

    def __exit__(self, *_args):
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio    # free up some memory
        sys.stdout = self._stdout


# Define the ages you're interested in
AGES = ["now", "1 month ago", "2 months ago", "3 months ago", "4 months ago", "5 months ago", "6 months ago"]

# Path to the Git repository
REPO_PATH = "/Users/fprior/Development/GitFarm/workplace/fprior/update-mirror-3/update-mirror/src/AWSDocsSdkExamplesPublic"

# Path to the YAML file you want to extract from each commit
FILE_PATH = "tools/update_mirror/config.yaml"


def get_commit_hash_for_age(git, age):
    """
    Get the commit hash for a specific age in the repository's history.

    Args:
        repo_dir (str): The path to the Git repository.
        age (str): The age to search for (e.g., '1 month ago').

    Returns:
        str: The commit hash corresponding to the specified age, or None if not found.
    """
    str(git('rev-list', '-1', f"--before={age}", 'HEAD', capture_output=True).stdout)


def run_commands_in_repo(git, commit_hash, age):
    """
    Run Git log and a Python command in a specific commit of a repository.

    Args:
        git (Sh(git)): an shgit with the repo loaded as its CWD
        commit_hash (str): The commit hash to run the commands in.
        age (str): The age of the commit being processed.
    """
    # Checkout repo at the specific commit
    git.checkout("--force", commit_hash)

    # Retrieve commit details
    log_output = str(git('log', '-n', '1', commit_hash, pretty='format:"%H|%an|%aI"', capture_output=True).stdout)

    if log_output:
        hash, name, date = log_output.split('|')

        print(f"{Fore.MAGENTA}Commit for {age}: {hash}, Author: {name}, Date: {date}")

        # Run the Python command on the repository
        print(f"{Fore.CYAN}Running stats command for repository: {git.cwd}")
        with Capturing() as output:
            stats([git.cwd])
        if output:
            print(output)
        print("###########################")
    else:
        print(f"{Fore.RED}No commit found for {age} in {git.cwd}")


def get_file_from_commits_and_clone(git: Sh, file_path: str, ages):
    """
    Extract file contents from specific commits and clone repositories for each mirror.

    Args:
        repo_path (str): Path to the main repository.
        file_path (str): Path to the YAML file within the repository.
        ages (list): List of age ranges to retrieve commit hashes for.

    Returns:
        dict: A dictionary mapping each age to the mirrors section of the YAML file.
    """
    age_content_dict = {}
    cloned_repos: dict[str, Path] = {}  # To track cloned repositories and their directories

    # Create a tmp directory for the clones
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        # Fetch the config file from the main repository for each age
        for age in ages:
            print(f"{Style.BRIGHT}{Fore.BLUE}" + "#" * 61)
            print(f"{Style.BRIGHT}{Fore.BLUE}" + f" {age.upper()} ".center(61, "#"))
            print(f"{Style.BRIGHT}{Fore.BLUE}" + "#" * 61)

            # Get the commit hash for the main repository
            main_commit_hash = get_commit_hash_for_age(git, age)
            if not main_commit_hash:
                print(f"{Fore.RED}Skipping {age} because commit hash could not be retrieved for the main repository.")
                continue

            # Get the YAML configuration from that commit
            file_content = str(git.show(f"{main_commit_hash}:{file_path}").stdout)

            if file_content:
                try:
                    # Parse the YAML content
                    yaml_content = yaml.safe_load(file_content)

                    # Extract the mirrors section
                    mirrors = yaml_content.get('mirrors', {})
                    age_content_dict[age] = mirrors

                    # Clone or reuse repos for each mirror
                    for mirror_name, mirror_info in mirrors.items():
                        process_mirror(cloned_repos, tmp_dir, age, mirror_name, mirror_info)

                except yaml.YAMLError as exc:
                    print(f"{Fore.RED}Error parsing YAML file for {age}: {exc}")
            else:
                print(f"{Fore.RED}No file content found for commit {main_commit_hash} at {age}")

    return age_content_dict


def process_mirror(cloned_repos, tmp_dir: Path, age, mirror_name, mirror_info):
    repo_url = mirror_info.get('git_mirror')
    branch = mirror_info.get('branch')
    dir_name = mirror_info.get('dir')

    # Check if repo has already been cloned
    if repo_url not in cloned_repos:
        # If not, clone the repository to a subfolder in the temp directory
        clone_dir = tmp_dir/dir_name
        git = Sh('git', cwd=clone_dir)
        git.clone(repo_url, str(clone_dir))
        git.checkout(branch)

        # Mark this repo as cloned
        cloned_repos[repo_url] = clone_dir
    else:
        print(f"{Fore.YELLOW}Reusing cloned repository {repo_url} for mirror {mirror_name}.")

    git = Sh('git', cwd=cloned_repos[repo_url])
    # Get the specific commit hash for this repo at this age
    repo_commit_hash = get_commit_hash_for_age(git, age)
    if repo_commit_hash:
        # Run commands in the cloned repository for the specific commit hash
        run_commands_in_repo(git, repo_commit_hash, age)
    else:
        print(f"{Fore.YELLOW}Skipping {mirror_name} in {age} due to failure in retrieving commit hash.")


def display_age_content_dict(age_content_dict):
    """
    Display the mirrors section extracted from the YAML files, grouped by age.

    Args:
        age_content_dict (dict): A dictionary with age as keys and mirrors data as values.
    """
    print(f"{Style.BRIGHT}{Fore.GREEN}File contents grouped by age range:")
    for age, mirrors in age_content_dict.items():
        print(f"{Fore.YELLOW}Age: {age}")
        print(f"{Fore.CYAN}Mirrors:")
        for mirror_name, mirror_info in mirrors.items():
            print(f"{Fore.MAGENTA}  - {mirror_name}:")
            print(f"    {Fore.CYAN}git_mirror: {mirror_info.get('git_mirror')}")
            print(f"    {Fore.CYAN}branch: {mirror_info.get('branch')}")
            print(f"    {Fore.CYAN}dir: {mirror_info.get('dir')}")
        print("-----------------")


if __name__ == "__main__":
    # Get the contents from the commits and clone the repos.
    git = Sh('git', cwd=REPO_PATH)
    age_content_dict = get_file_from_commits_and_clone(git, FILE_PATH, AGES)

    # Display the contents in the dictionary format.
    display_age_content_dict(age_content_dict)
