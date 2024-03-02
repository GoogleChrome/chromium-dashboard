#!/bin/bash
# echo "waiting for backend to come up"
while [[ "$(curl --connect-timeout 2 -s -o /dev/null -w ''%{http_code}'' http://localhost:8080)" != "200" ]]; do
    echo ..
    sleep 10
done
# echo backend is up
