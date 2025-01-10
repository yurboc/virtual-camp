#!/bin/bash

# Prepare this file:
# sudo chmod a+x sync.sh
# ./sync.sh
id

# 1. Pull sources from remote repository
git pull

# 2. Restart services
sudo service virtualcamp-* restart

# 3. Done
echo Done: `date`

