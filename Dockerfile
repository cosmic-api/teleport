FROM ubuntu:trusty
RUN apt-get update
RUN apt-get install -y build-essential
RUN apt-get install -y python3-pip python3-lxml

RUN pip3 install sphinx==1.3.1
RUN pip3 install xml2rfc==2.5.0
RUN apt-get install -y nodejs nodejs-legacy npm

RUN apt-get install -y wget
RUN apt-get install -y unzip

RUN mkdir /build
ADD package.json /build/
WORKDIR /build
RUN npm install

ADD . /build/

RUN mkdir .cache
RUN make .cache/site.tar