import subprocess
import yaml
import tempfile
import os
from colorama import Fore, Style, init

# Initialize colorama for Windows compatibility (does nothing on Linux/macOS)
init(autoreset=True)

# Define the ages you're interested in
AGES = ["now", "1 month ago", "2 months ago", "3 months ago", "4 months ago", "5 months ago", "6 months ago"]

# Path to the Git repository
REPO_PATH = "/Users/fprior/Development/GitFarm/workplace/fprior/update-mirror-3/update-mirror/src/AWSDocsSdkExamplesPublic"

# Path to the YAML file you want to extract from each commit
FILE_PATH = "tools/update_mirror/config.yaml"

def run_git_command(command, cwd=None):
    """
    Run a Git command and return the output.

    Args:
        command (str): The Git command to run.
        cwd (str, optional): The directory to run the command in. Defaults to None.

    Returns:
        str: The output of the Git command, or None if an error occurred.
    """
    try:
        result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, shell=True)
        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, command, result.stderr)
        return result.stdout.strip()
    except Exception as e:
        print(f"{Fore.RED}Error running command: {command}\n{Fore.RED}Error: {e}")
        return None

def clone_or_reuse_repo(repo_url, branch, clone_dir):
    """
    Clone a Git repository if it doesn't already exist, or reuse the existing clone.

    Args:
        repo_url (str): The URL of the repository to clone.
        branch (str): The branch to check out.
        clone_dir (str): The directory to clone the repository into.
    """
    if os.path.exists(clone_dir):
        print(f"{Fore.YELLOW}Repository {repo_url} already cloned in {clone_dir}. Reusing existing clone.")
    else:
        print(f"{Fore.GREEN}Cloning repository {repo_url} into {clone_dir}...")
        clone_cmd = f"git clone {repo_url} {clone_dir}"
        run_git_command(clone_cmd)

        # Checkout the correct branch
        print(f"{Fore.CYAN}Checking out branch {branch} in {clone_dir}...")
        checkout_cmd = f"git checkout {branch}"
        run_git_command(checkout_cmd, cwd=clone_dir)

def get_commit_hash_for_age(repo_dir, age):
    """
    Get the commit hash for a specific age in the repository's history.

    Args:
        repo_dir (str): The path to the Git repository.
        age (str): The age to search for (e.g., '1 month ago').

    Returns:
        str: The commit hash corresponding to the specified age, or None if not found.
    """
    log_cmd = f'git rev-list -1 --before="{age}" HEAD'
    commit_hash = run_git_command(log_cmd, cwd=repo_dir)
    if commit_hash:
        return commit_hash
    else:
        print(f"{Fore.RED}Failed to find commit hash for {age} in {repo_dir}")
        return None

def checkout_commit(repo_dir, commit_hash):
    """
    Checkout a specific commit hash in the repository.

    Args:
        repo_dir (str): The path to the Git repository.
        commit_hash (str): The commit hash to checkout.
    """
    print(f"{Fore.CYAN}Checking out commit {commit_hash} in {repo_dir}")
    checkout_cmd = f'git checkout --force {commit_hash}'
    run_git_command(checkout_cmd, cwd=repo_dir)

def run_commands_in_repo(repo_dir, commit_hash, age):
    """
    Run Git log and a Python command in a specific commit of a repository.

    Args:
        repo_dir (str): The path to the repository.
        commit_hash (str): The commit hash to run the commands in.
        age (str): The age of the commit being processed.
    """
    # Checkout the repository to the specific commit
    checkout_commit(repo_dir, commit_hash)

    # Retrieve the commit details
    log_cmd = f'git log -n 1 {commit_hash} --pretty=format:"%H|%an|%aI"'
    log_output = run_git_command(log_cmd, cwd=repo_dir)

    if log_output:
        log_parts = log_output.split('|')
        commit_hash = log_parts[0]
        author_name = log_parts[1]
        commit_date = log_parts[2]

        print(f"{Fore.MAGENTA}Commit for {age}: {commit_hash}, Author: {author_name}, Date: {commit_date}")

        # Run the Python command on the repository
        python_cmd = f'python3 -m aws_doc_sdk_examples_tools.stats "{repo_dir}"'
        print(f"{Fore.CYAN}Running stats command for repository: {repo_dir}")
        output = run_git_command(python_cmd, cwd=repo_dir)
        if output:
            print(output)
        print("###########################")
    else:
        print(f"{Fore.RED}No commit found for {age} in {repo_dir}")

def get_file_from_commits_and_clone(repo_path, file_path, ages):
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
    cloned_repos = {}  # To track cloned repositories and their directories

    # Create a temporary directory for the clones
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Fetch the configuration file from the main repository for each age
        for age in ages:
            print(f"{Style.BRIGHT}{Fore.BLUE}#############################################################")
            print(f"{Style.BRIGHT}{Fore.BLUE}######################## {age.upper()} ##############################")
            print(f"{Style.BRIGHT}{Fore.BLUE}#############################################################")

            # Get the commit hash for the main repository
            main_commit_hash = get_commit_hash_for_age(repo_path, age)
            if not main_commit_hash:
                print(f"{Fore.RED}Skipping {age} because commit hash could not be retrieved for the main repository.")
                continue

            # Get the YAML configuration from that commit
            file_content = run_git_command(f"git show {main_commit_hash}:{file_path}", cwd=repo_path)

            if file_content:
                try:
                    # Parse the YAML content
                    yaml_content = yaml.safe_load(file_content)

                    # Extract the mirrors section
                    mirrors = yaml_content.get('mirrors', {})
                    age_content_dict[age] = mirrors

                    # Clone or reuse repositories for each mirror
                    for mirror_name, mirror_info in mirrors.items():
                        repo_url = mirror_info.get('git_mirror')
                        branch = mirror_info.get('branch')
                        dir_name = mirror_info.get('dir')

                        # Check if this repository has already been cloned
                        if repo_url not in cloned_repos:
                            # If not, clone the repository to a subfolder in the temp directory
                            clone_dir = os.path.join(tmp_dir, dir_name)
                            clone_or_reuse_repo(repo_url, branch, clone_dir)

                            # Mark this repo as cloned
                            cloned_repos[repo_url] = clone_dir
                        else:
                            print(f"{Fore.YELLOW}Reusing cloned repository {repo_url} for mirror {mirror_name}.")

                        # Get the specific commit hash for this repo at this age
                        repo_commit_hash = get_commit_hash_for_age(cloned_repos[repo_url], age)
                        if repo_commit_hash:
                            # Run commands in the cloned repository for the specific commit hash
                            run_commands_in_repo(cloned_repos[repo_url], repo_commit_hash, age)
                        else:
                            print(f"{Fore.RED}Skipping {mirror_name} in {age} due to failure in retrieving commit hash.")

                except yaml.YAMLError as exc:
                    print(f"{Fore.RED}Error parsing YAML file for {age}: {exc}")
            else:
                print(f"{Fore.RED}No file content found for commit {main_commit_hash} at {age}")

    return age_content_dict

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
    # Get the contents from the commits and clone the repos
    age_content_dict = get_file_from_commits_and_clone(REPO_PATH, FILE_PATH, AGES)

    # Display the contents in the dictionary format
    display_age_content_dict(age_content_dict)
