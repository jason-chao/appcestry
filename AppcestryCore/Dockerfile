FROM jasonthc/appcestry-base:0.0.1b

# This is the Dockerfile for the core container image which contains all programme files for Appcestry.
# This container inherits the base container.
# The following tasks are performed:
#  - setting application-level environment variables
#  - copying programme files to the container image and setting their permissions
# This core container image contains the essential programme files for Appcestry.
# What exactly an instance of this container will play depends on the entry point or command specified in the docker-compose file

ENV APPCESTRY_DASK_SCHEDULER 127.0.0.1:8786
ENV APPCESTRY_HTTP_SERVER http://127.0.0.1:8899
ENV APPCESTRY_HTTP_LISTENING_ADDR 0.0.0.0
ENV APPCESTRY_HTTP_LISTENING_PORT 8899
ENV APPCESTRY_REDIS  redis://127.0.0.1:6379

ENV APPCESTRY_CORE_DIR /appcestry
ENV PATH "${APPCESTRY_CORE_DIR}:${PATH}"
ENV PYTHONPATH "${APPCESTRY_CORE_DIR}:${PYTHONPATH}"

COPY *.py ./
COPY Smali* ./
COPY rq_worker_*.sh ./
COPY dask_*.sh ./
RUN chmod a+x ./*.py
RUN chmod a+x ./*.sh
RUN python3 -m compileall .
CMD ["/bin/bash"]
