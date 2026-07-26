FROM apache/superset:6.1.0@sha256:fb3464528ec7076f91195f0ff7835755aa023e281f1bb78a84782ce7a36b3705

USER "0"

RUN apt-get update \
    && apt-get upgrade --yes \
    && apt-get purge --yes \
      libc-dev-bin \
      libc6-dev \
      libcrypt-dev \
      libecpg-dev \
      libldap-dev \
      libldap2-dev \
      libnsl-dev \
      libpq-dev \
      libsasl2-dev \
      libssl-dev \
      libtirpc-dev \
      linux-libc-dev \
    && apt-get autoremove --yes \
    && rm -rf /var/lib/apt/lists/*

RUN uv pip install --python /app/.venv/bin/python --upgrade \
      'Mako>=1.3.12' \
      'PyJWT>=2.13.0' \
      'cryptography==46.0.5' \
      'pillow>=12.3.0' \
      'pyOpenSSL>=26.0.0' \
      'pyasn1>=0.6.4' \
      'urllib3>=2.7.0' \
      'setuptools>=80.9.0' \
    && uv pip install --python /usr/local/bin/python --upgrade \
      'setuptools>=80.9.0' \
      'wheel>=0.46.2' \
    && uv pip check --python /app/.venv/bin/python \
    && rm -f /usr/local/bin/uv /usr/local/bin/uvx

USER "1000"
