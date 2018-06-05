#!/usr/bin/env bash

cd /appcestry
rq worker compare --url ${APPCESTRY_REDIS}
