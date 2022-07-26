FROM postgres:14-alpine
LABEL maintainer="Jordan Gould <jordangould@gmail.com>"
# Based on https://github.com/andreaswachowski/docker-postgres/blob/master/initdb.sh

ENV PG_JOBMON_VERSION v1.4.1
ENV PG_PARTMAN_VERSION v4.6.0

# Install pg_jobmon
RUN set -ex \
    \
    && apk add --no-cache --virtual .fetch-deps \
        ca-certificates \
        openssl \
        tar \
        && apk add --no-cache --virtual .build-deps \
        autoconf \
        automake \
        g++ \
        clang \
        llvm \
        libtool \
        libxml2-dev \
        make \
        perl

# Install pg_partman
RUN set -ex \
    && wget -O pg_partman.tar.gz "https://github.com/pgpartman/pg_partman/archive/$PG_PARTMAN_VERSION.tar.gz" \
    && mkdir -p /usr/src/pg_partman \
    && tar \
        --extract \
        --file pg_partman.tar.gz \
        --directory /usr/src/pg_partman \
        --strip-components 1 \
    && rm pg_partman.tar.gz \
    && cd /usr/src/pg_partman \
    && make \
    && make install \
    && cd / \
    && rm -rf /usr/src/pg_partman \
    && apk del .fetch-deps .build-deps

# Copy the init script
# The Docker Postgres initd script will run anything
# in the directory /docker-entrypoint-initdb.d
COPY docker_config/postgres/initdb.sh /docker-entrypoint-initdb.d/initdb.sh