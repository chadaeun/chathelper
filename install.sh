#!/usr/bin/env bash

apt-get -y update

# install docker
apt-get -y install docker
# build docker
docker build chatbot_manage/coala --tag coala:latest

# install gettext
apt-get -y install gettext

# install python
apt-get install software-properties-common
add-apt-repository ppa:deadsnakes/ppa
apt-get update
apt-get -y install python3.6

# create venv
pip install virtualenv
python3 -m virtualenv venv
venv/bin/pip3 install -r pipfreeze.txt
