#!/usr/bin/env bash

apt-get -y update
apt install -y build-essential

# install docker
apt-get -y install docker
# build docker
docker build chatbot_manage/coala --tag coala:latest

# install gettext
apt-get -y install gettext

# install python
apt-get -y install software-properties-common
add-apt-repository ppa:deadsnakes/ppa -y
apt-get -y update
apt-get -y install python3.6
apt-get -y install libxml2-dev libxslt-dev python3.6-dev

# install pip
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3.6 get-pip.py

# create venv
apt-get -y install libjpeg-dev
pip install virtualenv
python3.6 -m virtualenv venv
venv/bin/easy_install Pillow
venv/bin/pip install -r pipfreeze.txt
