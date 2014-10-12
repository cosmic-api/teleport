FROM ubuntu:14.04
RUN apt-get update
RUN apt-get install -y python-pip
RUN apt-get install -y nodejs nodejs-legacy npm

