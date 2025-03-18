#!/bin/sh

set -ex

die() {
    echo $* >&2
    exit 1
}

DEVELOP_BRANCH=develop

if [ "x$(git rev-parse --abbrev-ref HEAD)" != "x$DEVELOP_BRANCH" ]; then
    die "ERROR: Must be on $DEVELOP_BRANCH branch"
fi

OLD_PACKAGE_VERSION=$(awk '/^version = /{print $3}' setup.cfg)

$EDITOR setup.cfg || die "Not edited"

PACKAGE_VERSION=$(awk '/^version = /{print $3}' setup.cfg)

if [ "$OLD_PACKAGE_VERSION" = "$PACKAGE_VERSION" ]; then
    die "Version has not changed"
fi

git log "v${OLD_PACKAGE_VERSION}...HEAD" --format="COMMIT: %H%n%s%n%b" |
    ./tools/changelog new-entry "$PACKAGE_VERSION"

git commit -m "Version bump $PACKAGE_VERSION" setup.cfg docs/changelog.rst ||
    die "Commit failed"

git show

git push upstream $DEVELOP_BRANCH ||
    die "Failed to push upstream $DEVELOP_BRANCH"

make build-package-$PACKAGE_VERSION ||
    die "Build package failed"

git tag v$PACKAGE_VERSION ||
    die "Failed to create git tag"
git push upstream v$PACKAGE_VERSION ||
    die "Failed to push upstream tag"
