#!/bin/bash

set -e

case "$(uname -m)" in
    x86_64)   ARCH=x64 ;;
esac

case "$OSTYPE" in
    linux*)   PLATFORM=linux ;;
    msys*)    PLATFORM=win32 ;;
esac

echo "arch: $ARCH"
echo "platform: $PLATFORM"

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(git rev-parse --show-toplevel)"

CONAN_REF="jaysinco/stable"
CONAN_PROFILE="$PROJECT_ROOT/config/$PLATFORM/$ARCH/conan.profile"
CONAN_CONF="tools.cmake.cmaketoolchain:generator=Ninja"

if [ $PLATFORM = "linux" ]; then
    SOURCE_REPO="$PROJECT_ROOT/src"
elif [ $PLATFORM = "win32" ]; then
    SOURCE_REPO="$HOME/OneDrive/src"
fi

export JAYSINCO_SOURCE_REPO=$SOURCE_REPO
export CONAN_LOG_RUN_TO_FILE=1

function conan_source() {
    conan source .
}

function conan_install() {
    conan install \
        --profile=$CONAN_PROFILE \
        --profile:build=$CONAN_PROFILE \
        --install-folder=out \
        --conf=$CONAN_CONF \
        --build=never \
        . $CONAN_REF
}

function conan_build() {
    conan build \
        --install-folder=out \
        .
}

function conan_export_pkg() {
    conan export-pkg \
        --force \
        . $CONAN_REF
}

function conan_export() {
    conan export . $CONAN_REF
}

function conan_create() {
    conan create \
        --profile=$CONAN_PROFILE \
        --profile:build=$CONAN_PROFILE \
        --conf=$CONAN_CONF \
        . $CONAN_REF
}

function clean_build() {
    git clean -fdx .
}

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            echo
            echo "Usage: build.sh [options]"
            echo
            echo "Options:"
            echo "  -s, --source        conan source"
            echo "  -i, --install       conan install"
            echo "  -b, --build         conan build"
            echo "  -e, --export-pkg    conan export-pkg"
            echo "      --export        conan export"
            echo "      --create        conan create"
            echo "  -c, --clean         clean build output"
            echo "  -h, --help          print command line options"
            echo
            exit 0
            ;;
        -s|--source)
            conan_source
            exit 0
            ;;
        -i|--install)
            conan_install
            exit 0
            ;;
        -b|--build)
            conan_build
            exit 0
            ;;
        -e|--export-pkg)
            conan_export_pkg
            exit 0
            ;;
        --export)
            conan_export
            exit 0
            ;;
        --create)
            conan_create
            exit 0
            ;;
        -c|--clean)
            clean_build
            exit 0
            ;;
        -*|--*)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

clean_build \
&& conan_source \
&& conan_install \
&& conan_build \
&& conan_export_pkg
