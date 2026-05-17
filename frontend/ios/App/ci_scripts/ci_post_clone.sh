#!/bin/sh
set -e

# Xcode Cloud runs this immediately after cloning the repo.
# Working dir at start is ios/App/ci_scripts. The frontend root is two levels up.

cd "$CI_PRIMARY_REPOSITORY_PATH/frontend"

# Xcode Cloud images ship with Homebrew preinstalled.
brew install node@20
export PATH="/opt/homebrew/opt/node@20/bin:$PATH"

npm ci
npx cap sync ios
