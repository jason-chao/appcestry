#!/usr/bin/env bash

docker run --name siAppcestry -it --rm -p 8080:8080 --add-host=appcestry-dask-scheduler:127.0.0.1 jasonthc/appcestry:0.0.1a
