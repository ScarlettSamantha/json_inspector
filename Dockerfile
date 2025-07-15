FROM ubuntu:24.04

LABEL name="json-inspector"

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update -qq \
    && apt-get install -y --no-install-recommends \
    software-properties-common \
    curl \
    python3-dev \
    git \
    build-essential \
    lsb-release \
    && add-apt-repository ppa:deadsnakes/ppa -y \
    && apt-get update -qq \
    && apt-get install -y --no-install-recommends \
    python3.13 \
    python3.13-dev \
    && curl -sS https://bootstrap.pypa.io/get-pip.py | python3.13 \
    && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.13 1 \
    && pip3 install --upgrade pip \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/
RUN pip3 install -r /tmp/requirements.txt \
    && pip3 install briefcase \
    && rm -rf /root/.cache/pip

WORKDIR /app
COPY . /app

ENTRYPOINT ["bash", "-lc"]
CMD ["python3 --version \
    && python3 -m briefcase update -r \
    && python3 -m briefcase update --update-resources \
    && python3 -m briefcase build linux \
    && python3 -m briefcase package linux \
    && mkdir -p builds \
    && cp dist/*.deb builds/"]