* Installation

For global installation install: git, github desktop, anaconda

** Create a user environment using anaconda

** Install necessary packages

> conda install numpy matplotlib scipy spyder jupyter pyqt
> conda install coverage pyqtgraph nose scikit-image qtpy graphviz
> pip install pyvisa
> conda install -c https://conda.binstar.org/menpo opencv3


** Clone the necessary GIT repositories

1) QCodes
2) QTT
3) VandersypenUsers
4) VandersypenSetups

The git links are:

https://github.com/qdev-dk/Qcodes.git
https://github.com/VandersypenQutech/qtt.git
https://github.com/VandersypenQutech/users.git
https://github.com/VandersypenQutech/stations.git

** Install packages

> cd [USERDIR]\Qcpdes; conda develop .\
> cd [USERDIR]\qtt; conda develop .\

Note: the following does NOT work with anaconda
## > python setup.py develop --user

** Create startup shortcuts

For Spyder one can use something like:

```
@echo off
echo "Starting spyder" 
call activate eendebakpt
d:
cd d:\users\eendebakpt
spyder --new-instance -w d:\users\eendebakpt 
#spyder --show-console --new-instance -w d:\users\eendebakpt --session=eendebakpt.session.tar 
call deactivate eendebakpt
```

For a notebook session:

```
@echo off
echo "Starting Jupyter notebook" 

call activate eendebakpt
d:
cd d:\users\eendebakpt
jupyter notebook
call deactivate eendebakpt
```
