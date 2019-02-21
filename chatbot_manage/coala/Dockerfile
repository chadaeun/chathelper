FROM neptuneml/tensorflow-1.4-gpu-py3:2.8.3

ENV PATH /usr/local/bin:$PATH
ENV LANG C.UTF-8

RUN apt-get update

# 기본 패키지들 설치
RUN apt-get update
RUN apt-get install -y software-properties-common
RUN apt-get update
RUN apt-get install -y git
RUN apt-get install -y tmux

# Install OpenJDK-8
RUN apt-get update && \
    apt-get install -y openjdk-8-jdk && \
    apt-get install -y ant && \
    apt-get clean;

# Fix certificate issues
RUN apt-get update && \
    apt-get install ca-certificates-java && \
    apt-get clean && \
    update-ca-certificates -f;

# NLTK
RUN pip3 install -U nltk

# Setup JAVA_HOME -- useful for docker commandline
ENV JAVA_HOME /usr/lib/jvm/java-8-openjdk-amd64/
RUN export JAVA_HOME

EXPOSE 8888

ADD pipfreeze.txt /python-docker/pipfreeze.txt

# 작업 디렉토리로 이동
WORKDIR /python-docker

# 작업 디렉토리에 있는 requirements.txt로 패키지 설치
RUN pip3 install --upgrade pip
RUN pip3 install -r pipfreeze.txt