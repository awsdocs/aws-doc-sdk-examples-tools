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

# VERSION and DATE have the format YYYY.WW.REV, where YYYY is the current year,
# WW is the current week, and REV is the number of releases this week.
# The next revision compares the two, in this way
# - If DATE is later than VERSION in all fields, accept date.
# - Otherwise, return VERSION, with one added to REV.
#
# THIS FUNCTION IS NOT TRANSITIVE! It must be called with
# `compare_versions CURRENT NEXT`
compare_versions() {
    IFS='.' read -r y1 w1 r1 <<< "$1"
    IFS='.' read -r y2 w2 r2 <<< "$2"

    if [ "$y1" -lt "$y2" ] || \
       [ "$w1" -lt "$w2" ] || \
       [ "$r1" -lt "$r2" ]; then
        echo "$2"
    else
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
    git tag $VERSION main
    git push origin $VERSION
    git push origin main
fi
