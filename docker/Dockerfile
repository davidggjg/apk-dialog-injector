FROM ubuntu:20.04

# עדכון והתקנת חבילות נדרשות
RUN apt update && apt install -y \
    openjdk-11-jdk \
    wget \
    git \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# התקנת apktool
RUN wget https://raw.githubusercontent.com/iBotPeaches/Apktool/master/scripts/linux/apktool -O /usr/local/bin/apktool && \
    chmod +x /usr/local/bin/apktool && \
    wget https://github.com/iBotPeaches/Apktool/releases/download/v2.9.3/apktool_2.9.3.jar -O /usr/local/bin/apktool.jar && \
    chmod +x /usr/local/bin/apktool.jar

# יצירת ספריית עבודה
WORKDIR /work

# העתקת קבצי הסקריפט והתבניות
COPY patch.py /patch.py
COPY entrypoint.sh /entrypoint.sh
COPY smali_templates/ /smali_templates/

# הפיכת entrypoint להרצה
RUN chmod +x /entrypoint.py /entrypoint.sh

# נקודת הכניסה
ENTRYPOINT ["/entrypoint.sh"]
