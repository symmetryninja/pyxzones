# Features to add and things to fix in pyxzones

## bugs

- [*] crash on lock screen and full screen apps
  - [ ] I've swallowed an exception in service.py line 172 ish  - should log, not swallow
- [*] if you click to a new window and immediately drag, it moves the previous window
- [*] you are able to "pyxzones" the desktop activity - should probably filter this so you cant!
  - [ ] fixed using magic strings :/ should fix
- [ ] when starting as a service, it starts up before login and crashes immediately
- [ ] for some reason some apps (thunderbird and linux mint settings) has a borderspacing?? should remove / make consistent

## Documentation

- [ ] dependancies install (possibly add it to the project toml?)
- [ ] create system service

## new features (easy)

- [ ] make a system service installer (project toml?)
- [ ] make it work without a mouse using global hot key combination "ctrl+alt+(1,2,3,etc)"
- [ ] window positions not remembered
- [ ] make it a mint extension with editor

## to test

- Multiple monitors
  - move between monitors
    - mouse
    - keyboard
      - overflow super + arrows
      - global hotkey above on focused monitor
- multiple workspaces
- above combinations

## Future features

- multiple profiles
  - different profiles per monitor
  - hotkeys for profiles per monitor
- it would be nice if it could be triggered by left drag and right mouse click like fancyzones
