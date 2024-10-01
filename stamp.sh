#!/bin/sh

set -e # Exit on errors
# set -x # Shell debugging

# First, check that we're on the main branch.
BRANCH=$(git rev-parse --abbrev-rev HEAD)
if [ "$BRANCH" != "main" ] ; then 
    echo "Not on main, exiting!" 
    # exit 1
fi 

# And check that the main branch is clean
STATUS=$(git status --porcelain)
if [ -n "${STATUS}" ] ; then
    echo "Repository is not clean, exiting!" 
    # exit 1
fi 

# And check that the REMOTE points to the -tools repo.
REMOTE="${REMOTE:origin}"
if [ "$(git remote get-url $REMOTE 2>/dev/null)" != "git@github.com:awsdocs/aws-doc-sdk-examples-tools.git" ] ; then
    echo "REMOTE=${REMOTE} is not set to git@github.com:awsdocs/aws-doc-sdk-examples-tools.git, please adjust accordingly and rerun."
    exit 1
fi

# CURRENT and NEXT have the format YYYY.WW.REV, where YYYY is the current year,
# WW is the current week, and REV is the number of releases this week.
# The next revision compares the two, in this way
# - If NEXT is later than CURRENT in any fields, accept NEXT.
# - Otherwise, return CURRENT, with one added to REV.
#
# THIS FUNCTION IS NOT TRANSITIVE! It must be called with
# `compare_versions CURRENT NEXT`
compare_versions() {
    if [[ "$1" < "$2" ]] ; then
        echo "$2"
    else
        IFS='.' read -r y1 w1 r1 <<< "$1"
        r1=$((r1 + 1))
        echo "${y1}.${w1}.${r1}"
    fi
}

# compare_versions 2024.44.4 2024.44.0 # 2024.44.5
# compare_versions 2024.44.4 2024.45.0 # 2024.45.0
# compare_versions 2024.44.4 2025.1.0 # 2025.1.0

CURRENT=$(grep version= setup.py | awk -F\" '{print $2}')
NEXT=$(date +%Y.%W.0)
VERSION=$(compare_versions "$CURRENT" "$NEXT")
echo "Releasing $VERSION..."
sed -i '' "/version=/ s/$CURRENT/$VERSION/" setup.py
git --no-pager diff
git add setup.py
git commit --message "Release ${VERSION}"

if [ "$1" == "--release" ] ; then
    git tag "$VERSION" main
    git push "$REMOTE" "$VERSION"
    git push "$REMOTE" main
fi
