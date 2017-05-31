all: build

PYTHON=python

build : Makefile utils_find_1st/find_1st.cpp
	$(PYTHON) setup.py build_ext 

cythonize : 

install:
	$(PYTHON) setup.py install

install-user:
	$(PYTHON) setup.py install --user

clean:
	$(PYTHON) setup.py clean -a