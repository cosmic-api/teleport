FROM ubuntu:vivid
RUN apt-get update
RUN apt-get install -y build-essential
RUN apt-get install -y wget unzip
RUN apt-get install -y python3 python3-pip python3-lxml

RUN pip3 install sphinx==1.3.1
RUN pip3 install xml2rfc==2.5.0

RUN apt-get install -y curl
RUN curl --silent --location https://deb.nodesource.com/setup_4.x | bash -

RUN apt-get install -y nodejs
RUN npm install npm -g

RUN apt-get install -y git

RUN mkdir /build
ADD package.json /build/
WORKDIR /build
RUN npm install

ADD . /build/

RUN mkdir .cache
RUN ./configure
RUN make .cache/site.tar
