FROM ubuntu:vivid
RUN apt-get update
RUN apt-get install -y build-essential git wget curl unzip
RUN apt-get install -y python3 python3-pip python3-lxml

RUN curl -sL https://deb.nodesource.com/setup_5.x | bash -
RUN apt-get install -y nodejs

RUN pip3 install sphinx==1.3.6
RUN pip3 install xml2rfc==2.5.1

RUN mkdir /build
ADD package.json /build/
WORKDIR /build
RUN npm install

ADD . /build/

RUN mkdir .cache
RUN ./configure
RUN make .cache/site.tar
