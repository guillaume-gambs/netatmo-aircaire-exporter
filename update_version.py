# update_version.py
import subprocess
import os

def get_git_info():
    try:
        commit_sha = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('ascii').strip()
        git_tag = subprocess.check_output(['git', 'describe', '--tags', '--always']).decode('ascii').strip()
        return commit_sha, git_tag
    except:
        return "unknown", "unknown"

def update_version_file():
    commit_sha, git_tag = get_git_info()
    
    with open('version.py', 'w') as f:
        f.write(f'__version__ = "{git_tag}"\n')
        f.write(f'__commit_sha__ = "{commit_sha}"\n')
        f.write(f'__git_tag__ = "{git_tag}"\n')

if __name__ == "__main__":
    update_version_file()
