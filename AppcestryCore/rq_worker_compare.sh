#!/usr/bin/env bash

# Worker instance for Redis Queue "compare" 

cd /appcestry
rq worker compare --url ${APPCESTRY_REDIS}
