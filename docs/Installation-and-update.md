### Installation

At the moment, the package can be installed from this repository [https://github.com/stanislav-web/OpenDoor](https://github.com/stanislav-web/OpenDoor)
Now being tested, and the next will be published in other sources, such as Pypi.
   
|  Python | Linux  |  OSX | Windows  |
|:-:|:-:|:-:|:-:|
|2.6|[![Build Status](https://travis-ci.org/stanislav-web/OpenDoor.svg?branch=master)](https://travis-ci.org/stanislav-web/OpenDoor)    | ?  | [![Build status](https://ci.appveyor.com/api/projects/status/3hmrb64ofdssi4qd?svg=true)](https://ci.appveyor.com/project/stanislav-web/opendoor)|
|2.7|[![Build Status](https://travis-ci.org/stanislav-web/OpenDoor.svg?branch=master)](https://travis-ci.org/stanislav-web/OpenDoor)    | ?  | [![Build status](https://ci.appveyor.com/api/projects/status/3hmrb64ofdssi4qd?svg=true)](https://ci.appveyor.com/project/stanislav-web/opendoor)|

  
   * **GNU Linux**

Clone repo. `master` - is the most actual branch which always has the latest updates
```
        git clone -b master https://github.com/stanislav-web/OpenDoor.git opendoor
        cd opendoor
```

Install dependencies (can run without sudoer)
```
        pip install -r requirements.txt
        chmod +x opendoor.py
```

Also, you have to install `socksipy` package if you'll use socks as proxy in future
```
        apt-get install python-socksipy
```
Try your fist launch
```
        python opendoor.py -h
```

   *  **Windows XP/7/8/10**
        
I would recommend you to install GUI for Git at first if you dont have pre installed Git on your laptop.
Please see [https://git-for-windows.github.io](https://git-for-windows.github.io)
Go to your Git bash and clone repo

```
        git clone -b master https://github.com/stanislav-web/OpenDoor.git opendoor
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
        C:\opendoor>python opendoor.py -h
```

   * **OSX**
        
[TODO] Docs is not complete because package wasn't tested for Mac

### Update

You have an update a package using `git pull origin master` inside or run update process from interface:
```
# GNU Linux
python opendoor.py --update
```
 
```
# Win
C:\opendoor>python opendoor.py --update
```