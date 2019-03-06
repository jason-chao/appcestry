FROM ubuntu:18.04

# This is the Dockerfile for the base container for Appcestry.
# The following tasks are performed:
#  - installation of all dependencies
#  - setting OS-level environment variables
#  - creation of directories needed

ENV APPCESTRY_CORE_DIR /appcestry
RUN mkdir ${APPCESTRY_CORE_DIR}
RUN mkdir /tmp/appcestry
WORKDIR ${APPCESTRY_CORE_DIR}
COPY . ./
RUN apt-get update && apt-get install apktool -y \
    wdiff=1.2.2-2 \
    python3=3.6.5-3 \
    python3-pip=9.0.1-2.3~ubuntu1 \
    openjdk-8-jre=8u171-b11-0ubuntu0.18.04.1 \
    apktool=2.3.1+dfsg-1 \
    locales=2.27-3ubuntu1
RUN pip3 install --requirement ./requirements.txt
RUN chmod 777 /tmp/appcestry
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8
CMD ["/bin/bash"]
