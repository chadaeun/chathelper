docker build chatbot_manage/coala --tag coala:latest
pip3 install virtualenv
python3 -m virtualenv venv
venv/bin/pip3 install -r pipfreeze.txt
