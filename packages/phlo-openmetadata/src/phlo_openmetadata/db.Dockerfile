FROM docker.getcollate.io/openmetadata/db:1.13.1@sha256:6659446dba183f1e9364602839dd999c06a83f7d2e905d1c3fb22a74f3e27288

RUN microdnf update -y --disablerepo=mysql-tools-community && \
    python3.9 -m pip install --no-cache-dir --upgrade \
      --target=/usr/lib/mysqlsh/lib/python3.9/site-packages \
      certifi==2026.7.22 \
      cryptography==49.0.0 \
      pyOpenSSL==26.3.0 && \
    rm -rf \
      /usr/lib/mysqlsh/lib/python3.9/site-packages/certifi-2022.9.24.dist-info \
      /usr/lib/mysqlsh/lib/python3.9/site-packages/cryptography-37.0.2.dist-info \
      /usr/lib/mysqlsh/lib/python3.9/site-packages/pyOpenSSL-22.0.0.dist-info && \
    microdnf clean all

USER mysql
