#!/usr/bin/env bash

cd /appcestry
dask-scheduler --preload ./executor.py
