#!/usr/bin/env bash

cd /appcestry
dask-worker --preload ./executor.py ${APPCESTRY_DASK_SCHEDULER}
