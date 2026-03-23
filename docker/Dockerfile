FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    openjdk-11-jdk \
    wget \
    git \
    python3 \
    python3-pip \
    zipalign \
    apksigner \
    && rm -rf /var/lib/apt/lists/*

RUN wget https://raw.githubusercontent.com/iBotPeaches/Apktool/master/scripts/linux/apktool \
      -O /usr/local/bin/apktool && \
    chmod +x /usr/local/bin/apktool && \
    wget https://github.com/iBotPeaches/Apktool/releases/download/v2.9.3/apktool_2.9.3.jar \
      -O /usr/local/bin/apktool.jar && \
    chmod +x /usr/local/bin/apktool.jar

WORKDIR /work

COPY patch.py /patch.py
COPY entrypoint.sh /entrypoint.sh
COPY smali_templates/ /smali_templates/

RUN chmod +x /patch.py /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
