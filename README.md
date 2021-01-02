```
     _______     _______  ____  ____          _   _
    |  __ \ \   / / ____|/ __ \|  _ \   /\   | \ | |
    | |__) \ \_/ / |  __| |  | | |_) | /  \  |  \| |
    |  ___/ \   /| | |_ | |  | |  _ < / /\ \ | . ` |
    | |      | | | |__| | |__| | |_) / ____ \| |\  |
    |_|      |_|  \_____|\____/|____/_/    \_\_| \_|
``` 
Yet another goboard with gtp and sgf support fun project


Images & Soundfiles
--------------------

are not my work: 

- https://github.com/jokkebk/jgoboard/blob/master/large/shinkaya.jpg
- http://www.publicdomainpictures.net/view-image.php?image=162737&picture=go-board-intersections
- https://upload.wikimedia.org/wikipedia/en/thumb/b/b6/Realistic_Go_Stone.svg/1024px-Realistic_Go_Stone.svg.png
- https://upload.wikimedia.org/wikipedia/en/thumb/2/20/Realistic_White_Go_Stone.svg/1024px-Realistic_White_Go_Stone.svg.png
- Soundfile from http://qgo.sourceforge.net/


TODO
-----

- More sgf commands
- Better gtp time support
- Settings Gui (Button does not do anything yet)
- Clock does not show how many byoyomi periods areleft
- Mode after copying gamewindows
- Some images are missing under windows
- Color of tree root 
- ...


Usage
-----

See `pygoban  --help` or `python -m pygoban --help`
A config file named pygoban.ini will be created
Gtp enginges may be added under the GTP section

```
    [GTP]
    gnugo = /usr/games/gnugo --mode gtp
    kata = /home/user/lib/katago gtp -model /home/user/lib/lizzie/target/foo.bin.gz
```

