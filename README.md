#PiPlay
Media control board and software for the Raspberry Pi 
Work in progress

Martin O'Hanlon
[www.stuffaboutcode.com](http://www.stuffaboutcode.com)

##intall

###install on volumio 1.x

```
sudo apt-get update
sudo apt-get upgrade

sudo apt-get install build-essentials

# install wiringpi
git clone git://git.drogon.net/wiringPi
cd wiringPi
./build

sudo apt-get install python-dev
sudo apt-get install python-pip

sudo pip install gpiozero

sudo pip install python-mpd2
```

