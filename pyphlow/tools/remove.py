#! /usr/bin/env python3
import os
import sys


def main(root: str):
    with open(os.path.join(root, "rejected.txt"), 'r') as f:
        rejected_files = f.read().splitlines()

    print(rejected_files)

    for file in rejected_files:
        old_path = os.path.join(root, file)
        new_path = os.path.join(root, f"9rejected/{file}")
        if os.path.exists(old_path):
            os.makedirs(os.path.dirname(new_path), exist_ok=True)
            os.rename(old_path, new_path)


if __name__ == '__main__':
    print(sys.argv[0], sys.argv[1])
    main(sys.argv[1])
