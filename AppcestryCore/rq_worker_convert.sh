#!/usr/bin/env bash

# Worker instance for Redis Queue "convert" 

cd /appcestry
rq worker convert --url ${APPCESTRY_REDIS}
