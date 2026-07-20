#!/bin/bash
set -e
export GO111MODULE=on
go test -c -o apitest.test
echo "built: apitest.test"
