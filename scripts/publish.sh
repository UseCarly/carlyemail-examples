#!/usr/bin/env sh
# Publish the current tree to the public repository as one commit.
#
#     scripts/publish.sh "Add the chaser example"
#
# This repository is the private working copy, with the full history. The
# public one — UseCarly/carlyemail-examples — gets one commit per release
# holding the tree as it is now, so readers see releases and not the work.
# Nothing here rewrites the public branch: each publish is a new commit on
# top of the last one, with no parent in this history.
set -eu

message=${1:?usage: scripts/publish.sh "message"}
git diff --quiet && git diff --cached --quiet || { echo "commit or stash your changes first"; exit 1; }

git fetch -q public main 2>/dev/null || true
tree=$(git rev-parse HEAD^{tree})
parent=$(git rev-parse -q --verify public/main 2>/dev/null || true)
if [ -n "$parent" ] && [ "$(git rev-parse "$parent^{tree}")" = "$tree" ]; then
  echo "public/main already has this tree"; exit 0
fi
commit=$(git commit-tree "$tree" ${parent:+-p "$parent"} -m "$message")
git push -q public "$commit:refs/heads/main"
echo "published $(git rev-parse --short "$commit") -> UseCarly/carlyemail-examples main"
