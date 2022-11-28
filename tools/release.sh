#!/bin/sh

die() {
    echo $* >&2
    exit 1
}

if [ "x$(git rev-parse --abbrev-ref HEAD)" != "xdevelop" ]; then
    die "Error: Must be on develop branch"
fi

OLD_PACKAGE_VERSION=$(awk '/^version = /{print $3}' setup.cfg)

$EDITOR setup.cfg || die "Not edited"

PACKAGE_VERSION=$(awk '/^version = /{print $3}' setup.cfg)

if [ "$OLD_PACKAGE_VERSION" = "$PACKAGE_VERSION" ]; then
    die "Version did not changed"
fi

git commit -am "Version bump $PACKAGE_VERSION" setup.cfg
git push upstream develop || die "Failed to push upstream develop"

make build-package-$PACKAGE_VERSION || die "Build package failed"

git tag v$PACKAGE_VERSION || die "Failed to create git tag"
git push upstream v$PACKAGE_VERSION || die "Failed to push upstream tag"
