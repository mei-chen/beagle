FROM node:14-alpine

WORKDIR /node/

COPY package*.json ./

RUN npm install

ADD . /node/

EXPOSE 4003