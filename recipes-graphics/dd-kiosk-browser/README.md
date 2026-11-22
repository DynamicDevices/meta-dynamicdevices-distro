# Chromium kiosk startup

The recipe enables `dd-kiosk-browser.service` at boot. It waits for Weston's
Wayland socket and opens the configured URL in the kiosk browser. The current
default is Taylor Swift's official *Shake It Off* YouTube watch page, requesting
muted autoplay and single-video looping (`loop=1&playlist=nfWlot6h_JM`).
YouTube player fullscreen is not requested. Playback still
depends on connectivity and YouTube's availability and browser policies.

## Change the startup page

On the device, edit the `DD_KIOSK_URL` line in
`/etc/default/dd-kiosk-browser`, for example with:

```sh
sudoedit /etc/default/dd-kiosk-browser
sudo systemctl restart dd-kiosk-browser.service
```

Keep the whole URL on one line. This file is read as a systemd environment
file, not sourced as a shell script. `DD_KIOSK_MUTE_AUDIO=1` preserves silent
startup. Changing that setting does not configure amplifier gain or routing.

The file is packaged as a configuration file. Existing device overrides may
survive an update; a recipe default alone does not prove an OTA changed a
device's URL. No `/tmp` page or `/run` override is required for this setup.

The recipe sets `DD_KIOSK_GLES2_COMPAT=1` only for
`imx8mm-jaguar-screen`, preserving the accepted Etnaviv/GC600 workaround without
changing other machines' GPU settings or disabling the browser sandbox.

## Local regression tests

```sh
python3 -m unittest discover -s recipes-graphics/dd-kiosk-browser -p 'test_*.py'
```

These tests exercise launcher arguments with a fake browser and Wayland socket
and check the recipe's startup/configuration contract. They do not replace a
Foundries image build, reboot test or real YouTube playback check.
