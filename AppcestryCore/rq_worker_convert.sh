#!/usr/bin/env bash

cd /appcestry
rq worker convert --url ${APPCESTRY_REDIS}
