FROM python:3.13.0-bookworm

RUN apt-get update
RUN apt-get -y upgrade
RUN apt-get -y install aptitude locate apt-file nano vim git zip unzip wget graphviz curl gnupg gnupg2 tini iputils-ping unixodbc-dev
RUN apt-get -y install gcc g++ flex bison pkg-config automake autoconf cmake
RUN apt-get -y install python3-dev python3-pydot python3-tk
RUN apt-get -y install libopenblas-dev liblapack-dev libboost-all-dev libncurses5-dev libtool libssl-dev libjemalloc-dev libboost-dev libboost-filesystem-dev libboost-system-dev libboost-regex-dev libxml2-dev libxslt-dev libfreetype6-dev libsuitesparse-dev libclang-16-dev llvm-16-dev libthrift-dev libfftw3-dev
RUN python3 -m pip install --upgrade pip
RUN pip3 install deprecation==2.1.0 graphviz==0.20.3 intervaltree==3.1.0 networkx==3.4.2 packaging==24.2 python-dateutil==2.9.0.post0 pytz==2024.2 setuptools==75.7.0 six==1.17.0 sortedcontainers==2.4.0 tzdata==2024.2 wheel==0.45.1 
RUN pip3 install colorama==0.4.6 cycler==0.12.1 pydotplus==2.0.2 pyparsing==3.2.1 tqdm==4.67.1 
RUN pip3 install lxml==5.3.0 numpy==2.2.1 pandas==2.2.3 scipy==1.15.0 
RUN pip3 install contourpy==1.3.1 fonttools==4.55.3 kiwisolver==1.4.8 matplotlib==3.10.0 pillow==11.1.0 
RUN pip3 install anyio==4.8.0 attrs==24.3.0 certifi==2024.12.14 charset-normalizer==3.4.1 distro==1.9.0 h11==0.14.0 httpcore==1.0.7 httpx==0.28.1 idna==3.10 jiter==0.8.2 jsonschema-specifications==2024.10.1 pydantic==2.10.4 referencing==0.35.1 rpds-py==0.22.3 sniffio==1.3.1 typing_extensions==4.12.2 urllib3==2.3.0 
RUN pip3 install jsonschema==4.23.0 openai==1.59.3 requests==2.32.3 
RUN pip3 install -U meson-python==0.15.0 Cython==3.0.10 ninja==1.11.1.1 spin==0.8 build==1.2.1 setuptools_scm==8.0.4

#RUN cd / && git clone https://github.com/numpy/numpy.git && cd /numpy && git submodule update --init && pip3 install .
#RUN cd / && git clone https://github.com/pandas-dev/pandas.git && cd /pandas && pip3 install .
#RUN cd / && git clone https://github.com/scipy/scipy.git && cd /scipy && git submodule update --init && pip3 install .
#RUN cd / && git clone https://github.com/lxml/lxml.git && cd /lxml && pip3 install .
#RUN cd / && git clone https://github.com/matplotlib/matplotlib.git && cd /matplotlib && pip3 install .
#RUN cd / && git clone https://github.com/duckdb/duckdb.git && cd /duckdb && make && cd /duckdb/tools/pythonpkg && pip3 install .
#RUN cd / && git clone https://github.com/apache/arrow.git && export ARROW_HOME=/dist && export LD_LIBRARY_PATH=/dist/lib:$LD_LIBRARY_PATH && export CMAKE_PREFIX_PATH=$ARROW_HOME:$CMAKE_PREFIX_PATH && cd /arrow/ && mkdir cpp/build && cd cpp/build && cmake -DCMAKE_INSTALL_PREFIX=$ARROW_HOME -DCMAKE_INSTALL_LIBDIR=lib -DCMAKE_BUILD_TYPE=Debug -DARROW_BUILD_TESTS=ON -DARROW_COMPUTE=ON -DARROW_CSV=ON -DARROW_DATASET=ON -DARROW_FILESYSTEM=ON -DARROW_HDFS=ON -DARROW_JSON=ON -DARROW_PARQUET=ON -DARROW_WITH_BROTLI=ON -DARROW_WITH_BZ2=ON -DARROW_WITH_LZ4=ON -DARROW_WITH_SNAPPY=ON -DARROW_WITH_ZLIB=ON -DARROW_WITH_ZSTD=ON -DPARQUET_REQUIRE_ENCRYPTION=ON .. && make -j4 && make install && cd /arrow/python && export PYARROW_WITH_PARQUET=1 && export PYARROW_WITH_DATASET=1 && export PYARROW_PARALLEL=4 && python3 setup.py build_ext --inplace && python3 setup.py install
#RUN cd / && git clone https://github.com/python-greenlet/greenlet && cd /greenlet && pip3 install .
#RUN cd / && git clone https://github.com/sqlalchemy/sqlalchemy.git && cd /sqlalchemy && pip3 install .
#RUN cd / && git clone https://github.com/mkleehammer/pyodbc.git && cd /pyodbc && pip3 install .

#RUN cd / && git clone https://github.com/scikit-learn/scikit-learn.git && cd /scikit-learn && pip3 install .
#RUN cd / && git clone https://github.com/chuanconggao/PrefixSpan-py.git && cd /PrefixSpan-py && pip3 install .
#RUN cd / && git clone https://github.com/wmayner/pyemd.git && cd /pyemd && pip3 install .
#RUN cd / && wget https://ftp.gnu.org/gnu/glpk/glpk-5.0.tar.gz && tar xzvf glpk-5.0.tar.gz && cd /glpk-5.0 && ./configure && make && make install
#RUN cd / && git clone https://github.com/cvxopt/cvxopt.git && cd /cvxopt && sed -i 's/BUILD_GLPK = 0/BUILD_GLPK = 1/' setup.py && python3 setup.py build && python3 setup.py install

COPY . /app
RUN cd /app && pip3 install --no-deps .
