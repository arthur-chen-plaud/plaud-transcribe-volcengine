FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ENV PIP_INDEX_URL=${PIP_INDEX_URL}
ENV PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn

RUN apt update && apt install -y \
    software-properties-common \
    curl \
    git \
    && add-apt-repository -y ppa:deadsnakes/ppa \
    && apt update -y \
    && apt install -y python3.12 python3.12-venv python3.12-dev \
    && apt clean && rm -rf /var/lib/apt/lists/*

RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.12
RUN ln -s /usr/bin/python3.12 /usr/bin/python && ln -s /usr/local/bin/pip /usr/bin/pip

WORKDIR /workspace
EXPOSE 8080

RUN apt-get update && \
    apt-get install -y --no-install-recommends supervisor && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ENV TimeZone=Etc/UTC
RUN ln -snf /usr/share/zoneinfo/$TimeZone /etc/localtime && echo $TimeZone > /etc/timezone

COPY requirements.txt /workspace/
COPY ./src/ /workspace/src/
COPY ./config.py /workspace/config.py
COPY ./run_celery.py /workspace/run_celery.py
COPY ./start_celery.sh /workspace/
RUN chmod +x /workspace/start_celery.sh

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["/workspace/start_celery.sh"]
