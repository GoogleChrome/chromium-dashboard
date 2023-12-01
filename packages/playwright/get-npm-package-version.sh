#!/bin/bash

# E.g. ./get-npm-package-version.sh packages/playwright/package.json "@playwright/test"

# Get the name of the devDependency
devDependency=$2

# Get the version number of the devDependency  ["$devDependency"]
version=$(jq -r '.devDependencies."'${devDependency}'"' $1)

# Print the version number
echo $version
