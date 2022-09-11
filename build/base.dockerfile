ARG FROM
FROM ${FROM}
RUN echo "Building Base Docker" && \
    # Install dependencies
    yum install gcc -y && \
    yum install perl -y && \
    yum install bzip2-devel -y && \
    yum install libffi-devel -y && \
    yum install zlib-devel -y && \
    yum install xz -y && \
    yum install tar -y && \
    yum install gzip -y && \
    yum install make -y && \

    # Install Node
    curl -sL https://rpm.nodesource.com/setup_14.x | bash - && \
    yum install nodejs -y && \

    # Install OpenSSL 1.1.1 (required by Python 3.10)
    cd /opt && \
    curl -O https://www.openssl.org/source/openssl-1.1.1q.tar.gz && \
    mkdir /opt/openssl && \
    tar xfvz openssl-1.1.1q.tar.gz --directory /opt/openssl && \
    cd /opt/openssl/openssl-1.1.1q/ && \
    ./config --prefix=/opt/openssl no-shared && \
    make && \
    make install_sw && \

    # Install Python 3.10.7
    cd /opt && \
    curl -O https://www.python.org/ftp/python/3.10.7/Python-3.10.7.tgz && \
    tar -xzf Python-3.10.7.tgz && \
    cd Python-3.10.7 && \
    ./configure --enable-optimizations --enable-shared --prefix=/opt/python LDFLAGS=-Wl,-rpath=/opt/python/lib --with-openssl=/opt/openssl && \
    make -j$(nproc) altinstall && \
    ln -s /opt/python/bin/python3.10 /usr/local/bin/python3 && \

    # Clean files
    rm -rf /opt/openssl-1.1.1q.tar.gz && \
    rm -rf /opt/Python-3*