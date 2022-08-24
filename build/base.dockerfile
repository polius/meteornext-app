FROM amazonlinux:1
RUN echo "Building Base Docker" && \
    # Install dependencies
    yum install gcc -y && \
    yum install perl -y && \
    yum install bzip2-devel -y && \
    yum install libffi-devel -y && \
    yum install zlib-devel -y && \
    yum install xz -y && \

    # Install OpenSSL 1.1.1 (required by Python 3.10)
    cd /opt && \
    curl -O https://www.openssl.org/source/openssl-1.1.1q.tar.gz && \
    mkdir /opt/openssl && \
    tar xfvz openssl-1.1.1q.tar.gz --directory /opt/openssl && \
    cd /opt/openssl/openssl-1.1.1q/ && \
    ./config --prefix=/opt/openssl --openssldir=/opt/openssl/ssl && \
    make && \
    make install && \

    # Add openssl lib path to the library (required by the Python install)
    export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:/opt/openssl/lib && \

    # Install Python 3.10.6
    cd /opt && \
    curl -O https://www.python.org/ftp/python/3.10.6/Python-3.10.6.tgz && \
    tar -xzf Python-3.10.6.tgz && \
    cd Python-3.10.6 && \
    ./configure --enable-optimizations --enable-shared --prefix=/opt/python LDFLAGS=-Wl,-rpath=/opt/python/lib --with-openssl=/opt/openssl --with-openssl-rpath=auto && \
    make -j$(nproc) altinstall && \
    ln -s /opt/python/bin/python3.10 /usr/local/bin/python3 && \

    # Clean files
    rm -rf /opt/openssl-1.1.1q.tar.gz && \
    rm -rf /opt/Python-3*