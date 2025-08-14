FROM ubuntu:latest

# Paquetes base
RUN apt-get update && apt-get install -y \
    openjdk-17-jre-headless \
    python3-pip \
    curl bash-completion fontconfig fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# ANTLR jar
COPY antlr-4.13.1-complete.jar /usr/local/lib/antlr-4.13.1-complete.jar

# Scripts 'antlr' y 'grun' sin heredocs (evita el problema de quoting)
RUN printf '%s\n' '#!/usr/bin/env bash' \
  'exec java -Xmx500m -cp /usr/local/lib/antlr-4.13.1-complete.jar org.antlr.v4.Tool "$@"' \
  > /usr/local/bin/antlr && chmod +x /usr/local/bin/antlr

RUN printf '%s\n' '#!/usr/bin/env bash' \
  'exec java -Xmx500m -cp /usr/local/lib/antlr-4.13.1-complete.jar org.antlr.v4.gui.TestRig "$@"' \
  > /usr/local/bin/grun && chmod +x /usr/local/bin/grun

# Dependencias Python del repo
COPY requirements.txt /tmp/requirements.txt
RUN pip install --break-system-packages -r /tmp/requirements.txt

# Usuario no-root (opcional)
ARG USER=appuser
ARG UID=1001
RUN adduser --disabled-password --gecos "" --home /home/${USER} --uid "${UID}" "${USER}"
USER ${UID}

# Trabajar sobre /program (lo vas a montar)
WORKDIR /program