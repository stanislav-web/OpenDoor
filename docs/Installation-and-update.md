Installation
===============
Python v3.3 is minor requirement.
At the moment, the package can be installed from this repository [https://github.com/stanislav-web/OpenDoor](https://github.com/stanislav-web/OpenDoor)
Now being tested, and the next will be published in other sources, such as Pypi.

|  Python | Linux  |  OSX | Windows  |
|:-:|:-:|:-:|:-:|
|3.4|[![Build Status](https://travis-ci.org/stanislav-web/OpenDoor.svg?branch=master)](https://travis-ci.org/stanislav-web/OpenDoor)    | ?  | [![Build status](https://ci.appveyor.com/api/projects/status/3hmrb64ofdssi4qd?svg=true)](https://ci.appveyor.com/project/stanislav-web/opendoor)|
|3.5|[![Build Status](https://travis-ci.org/stanislav-web/OpenDoor.svg?branch=master)](https://travis-ci.org/stanislav-web/OpenDoor)    | ?  | [![Build status](https://ci.appveyor.com/api/projects/status/3hmrb64ofdssi4qd?svg=true)](https://ci.appveyor.com/project/stanislav-web/opendoor)|
|3.6|[![Build Status](https://travis-ci.org/stanislav-web/OpenDoor.svg?branch=master)](https://travis-ci.org/stanislav-web/OpenDoor)    | ?  | [![Build status](https://ci.appveyor.com/api/projects/status/3hmrb64ofdssi4qd?svg=true)](https://ci.appveyor.com/project/stanislav-web/opendoor)|

GNU Linux (Local installation and run)
---------------------------

```
 git clone https://github.com/stanislav-web/OpenDoor.git
 cd OpenDoor/
 pip install -r requirements.txt
 chmod +x opendoor.py

 python3 opendoor.py --host http://www.example.com
```

GNU Linux (Global. Preferably for OS distributions)
---------------------------

```
 git clone https://github.com/stanislav-web/OpenDoor.git
 cd OpenDoor/
 python3 setup.py build && python3 setup.py install

 opendoor --host http://www.example.com
```


Windows XP/7/8/10
---------------------------

I would recommend you to install GUI for Git at first if you dont have pre installed Git on your laptop.
Please see [https://git-for-windows.github.io](https://git-for-windows.github.io)
Go to your Git bash and clone repo

```
        git clone https://github.com/stanislav-web/OpenDoor.git opendoor
        cd opendoor
```

Next , install python package manager.
Here you go > [https://pip.pypa.io/en/stable/installing/#do-i-need-to-install-pip](https://pip.pypa.io/en/stable/installing/#do-i-need-to-install-pip)
Install dependencies

```
        C:\opendoor> pip install -r requirements.txt
```

Unfortunately, you can't use Socks proxy on Windows. HTTP(S) supported only
Try your fist launch

```
        C:\opendoor>python3 opendoor.py -h
```

OSX
---
   
[TODO] Docs is not complete because package wasn't tested for Mac

Dependencies
============
![Dependencies](images/dependencies.jpg)

Update
===============
You have an update a package using `git pull origin master` inside or run update process from interface:
```
# GNU Linux
python opendoor.py --update
```
 
```
# Win
C:\opendoor>python opendoor.py --update
```