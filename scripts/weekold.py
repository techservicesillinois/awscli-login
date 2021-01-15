import argparse
import os
import sys
import time

WEEK = 60 * 60 * 24 * 7

def done(old: bool):
    # https://docs.github.com/en/free-pro-team@latest/actions/reference/workflow-commands-for-github-actions#using-workflow-commands-to-access-toolkit-functions
    github_workflow_cmd = "::set-output name=weekold::"

    print(github_workflow_cmd, old, sep='')
    print("Are any of the files one week old or older?", old, file=sys.stderr)
    exit(int(old))

def main():
    parser = argparse.ArgumentParser(description='Test if all file '
        'arguments are at least one week old.')
    parser.add_argument('files', metavar='FILE', nargs='+',
        help='a file to be tested.')
    args = parser.parse_args()

    now = time.time()
    for filename in args.files:
        age = now - os.stat(filename).st_mtime
        if age < WEEK:
            done(False)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e, file=sys.stderr)

    done(True)
