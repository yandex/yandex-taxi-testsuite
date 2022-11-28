#!/bin/sh

set -ex

TESTSUITE_GH_PAGES_REPO="$1"
PACKAGE_VERSION="$2"

run_git() {
    git -C "$TESTSUITE_GH_PAGES_REPO" "$@"
}

if [ "x$TESTSUITE_GH_PAGES_REPO" = "x" ]; then
    echo "TESTSUITE_GH_PAGES_REPO must be set" >&2;
    exit 1
fi

if [ ! -d "$TESTSUITE_GH_PAGES_REPO" ]; then
    mkdir -p "$TESTSUITE_GH_PAGES_REPO"
    run_git init
    run_git remote add upstream git@github.com:yandex/yandex-taxi-testsuite.git
fi

run_git fetch upstream gh-pages
run_git checkout gh-pages
run_git reset --hard upstream/gh-pages
run_git clean -fxd
cp -R docs/_build/dirhtml/* "$TESTSUITE_GH_PAGES_REPO"
touch "$TESTSUITE_GH_PAGES_REPO/.nojekyll"
run_git add "$TESTSUITE_GH_PAGES_REPO/*"
if run_git commit -am "Update docs version $PACKAGE_VERSION"; then
    run_git push upstream gh-pages
fi
