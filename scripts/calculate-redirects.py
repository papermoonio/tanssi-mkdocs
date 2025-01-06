# ------------- 👋 Welcome to the script for calculating redirect mappings ---------------#
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
# The purpose of this script is to calculate redirect mappings for the `mkdocs.yml` file. #
# The script works by looking at the current file directory in the `main` branch and on   #
# your local branch. It compares the two file structures to see if content has been moved #
# at all. If any content has been moved, the script will try to match the moved content   #
# and add it to the `redirect_maps` config in `mkdocs.yml`.                               #
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
# Make sure you have ssh enabled in GitHub before running this script. Otherwise, you'll  #
# receive a 403 from the GitHub API when you run the script.                              #
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
# To use the script, ensure that the `tanssi-docs` repo is nestled inside of the          #
# `tanssi-mkdocs` repo and on your branch with the latest changes. Then simply run        #
# `python scripts/calculate-redirects.py <base_branch> <compare_branch>` in your terminal.#
#                                                                                         #
# Command-line arguments:                                                                 #
#   - `base_branch`: Base branch name (e.g., `main`)                                      #
#   - `compare_branch`: Compare branch name (e.g., `new_branch`)                          #
#                                                                                         #
# Example usage:                                                                          #
#   python scripts/calculate-redirects.py main new_branch                                 #
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

import os
import yaml
import argparse
import requests
from yaml.nodes import ScalarNode, SequenceNode


def update_redirects(redirect_mappings, yaml_file):
    # Open the YAML file and read its lines
    with open(yaml_file, "r") as file:
        lines = file.readlines()

    # Initialize a flag to track if the redirect_maps section is found
    redirect_maps_found = False
    redirect_maps_start = -1
    redirect_maps_end = -1

    # Find the start and end indices of the redirect_maps section
    for i, line in enumerate(lines):
        if "redirect_maps" in line:
            redirect_maps_found = True
            redirect_maps_start = i + 1  # Start after the redirect_maps line
        elif redirect_maps_start != -1 and line.strip() == "- macros:":
            redirect_maps_end = i
            break

    # If redirect_maps section is found, delete the old mappings
    if redirect_maps_found:
        del lines[redirect_maps_start:redirect_maps_end]

    # Sort the redirect mappings by keys
    sorted_redirect_mappings = dict(sorted(redirect_mappings.items()))

    # Insert the new mappings
    if sorted_redirect_mappings:
        if not redirect_maps_found:
            # Find the index of the last line before the plugins section
            plugins_index = lines.index("plugins:\n") + 1
            # Insert redirect_maps section before the plugins section
            lines.insert(plugins_index, "  - redirects:\n")
            lines.insert(plugins_index + 1, "      redirect_maps:\n")

        # Find the index of the redirect_maps section
        redirect_maps_index = lines.index("      redirect_maps:\n") + 1

        # Insert the sorted redirect mappings
        for source, destination in sorted_redirect_mappings.items():
            mapping_line = f"        {source}: {destination}\n"
            lines.insert(redirect_maps_index, mapping_line)
            redirect_maps_index += 1

    # Write the updated lines back to the file
    with open(yaml_file, "w") as file:
        file.writelines(lines)

    print("✅ Process complete! You can review the redirects in the mkdocs.yml file")


# Function to check if a file name is a key or a value
def check_file_in_redirects(file_name, redirects):
    for key, value in redirects.items():
        if file_name == value:
            return key, value
    return None


# Function to generate redirects
def generate_redirects(github_repo, base_branch, compare_branch):
    # Load existing redirects from mkdocs.yml
    mkdocs_yaml_path = "mkdocs.yml"
    redirects = load_redirects_from_mkdocs(mkdocs_yaml_path)

    # Get list of changed files on the compare_branch compared to the base_branch
    compare_commit = get_commit_sha(github_repo, compare_branch)
    base_commit = get_commit_sha(github_repo, base_branch)
    comparison = get_commit_comparison(github_repo, base_commit, compare_commit)
    for file in comparison["files"]:
        filename = file["filename"]
        if filename.endswith(".md") and ".snippets" not in filename:
            if file["status"] == "removed":
                result = check_file_in_redirects(filename, redirects)
                if result:
                    key, value = result
                    print(
                        f"❌ New page to redirect to cannot be found for: {filename}, so index.md was used as a fallback. Please review and update the redirect manually if needed."
                    )
                    redirects[key] = "index.md # TODO: Double-check me!"  # Set the original redirect to index.md
                    redirects[value] = (
                        "index.md # TODO: Double-check me!"  # Set the redirected redirect to index.md
                    )
                else:
                    # Create a new redirect
                    print(
                        f"❌ New page to redirect to cannot be found for: {filename}, so index.md was used as a fallback. Please review and update the redirect manually if needed."
                    )
                    redirects[filename] = "index.md # TODO: Double-check me!"
            elif file["status"] == "renamed":
                prev_file = file["previous_filename"]
                result = check_file_in_redirects(prev_file, redirects)
                if result:
                    key, value = result
                    redirects[key] = (
                        filename  # Set the original redirect to the new file name
                    )
                    redirects[value] = (
                        filename  # Set the redirected redirect to the new file name
                    )
                else:
                    redirects[prev_file] = filename

    # Save updated redirects to mkdocs.yml
    update_redirects(redirects, mkdocs_yaml_path)


# Define custom constructor for !ENV tag
def env_constructor(loader, node):
    if isinstance(node, ScalarNode):  # Handle simple scalar values
        value = loader.construct_scalar(node)
        return os.getenv(value, "") or value
    elif isinstance(node, SequenceNode):  # Handle sequences like `[VAR, default]`
        values = loader.construct_sequence(node)
        if len(values) == 2:
            env_var, default_value = values
            return os.getenv(env_var, default_value)
        raise ValueError(
            "!ENV sequence must have exactly two elements: [ENV_VAR, default_value]"
        )
    raise ValueError("Unsupported YAML node type for !ENV")


# Add the custom constructor to the SafeLoader
yaml.SafeLoader.add_constructor("!ENV", env_constructor)


# Ignore unknown entries in the yaml file
def ignore_unknown(loader, tag_suffix, node):
    return None


yaml.SafeLoader.add_multi_constructor("tag:yaml.org,2002:python/", ignore_unknown)


# Function to load redirects from mkdocs.yml
def load_redirects_from_mkdocs(mkdocs_yaml_file):
    redirects = {}
    if os.path.exists(mkdocs_yaml_file):
        with open(mkdocs_yaml_file, "r") as file:
            mkdocs_config = yaml.load(file, Loader=yaml.SafeLoader)
            for plugin in mkdocs_config.get("plugins", []):
                if isinstance(plugin, dict) and "redirects" in plugin:
                    redirects = plugin["redirects"].get("redirect_maps", {})
                    break
    return redirects


# Function to get commit SHA for a given branch
def get_commit_sha(github_repo, branch):
    url = f"https://api.github.com/repos/{github_repo}/commits/{branch}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()["sha"]


# Function to get commit comparison between two commits
def get_commit_comparison(github_repo, base_commit, compare_commit):
    url = f"https://api.github.com/repos/{github_repo}/compare/{base_commit}...{compare_commit}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    # Create argument parser
    parser = argparse.ArgumentParser(
        description="Generate redirects for changed files in a GitHub repository."
    )
    parser.add_argument("base_branch", type=str, help="Base branch name (e.g., main)")
    parser.add_argument(
        "compare_branch", type=str, help="Compare branch name (e.g., new_branch)"
    )

    # Parse arguments
    args = parser.parse_args()

    # Generate redirects
    print("⏱️ Generating redirects... just a few moments...")
    generate_redirects(
        "moondance-labs/tanssi-docs", args.base_branch, args.compare_branch
    )
