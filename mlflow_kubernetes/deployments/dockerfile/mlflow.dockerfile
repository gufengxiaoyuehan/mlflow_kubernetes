FROM ubuntu:18.04
RUN apt-get -y update && apt-get install -y --no-install-recommends \
         wget \
         curl \
         nginx \
         ca-certificates \
         bzip2 \
         build-essential \
         cmake \
         openjdk-8-jdk \
         git-core \
         maven \
    && rm -rf /var/lib/apt/lists/*

# Download and setup miniconda
RUN curl -L https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh >> miniconda.sh
RUN bash ./miniconda.sh -b -p /miniconda; rm ./miniconda.sh;
ENV PATH="/miniconda/bin:$PATH"
ENV JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
ENV GUNICORN_CMD_ARGS="--timeout 60 -k gevent"
ADD mirrors/settings.xml /etc/maven/settings.xml
ADD mirrors/.condarc /etc/conda/.condarc
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
