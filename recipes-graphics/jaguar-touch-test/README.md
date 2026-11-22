# Jaguar touch and gesture test

`jaguar-touch-test_1.0.bb` installs the page and launcher. The kiosk-browser image
feature includes this package for `imx8mm-jaguar-screen`; installation does not
replace the configured boot URL or change touchscreen calibration.

Launch `jaguar-touch-test --gestures` from the existing Weston user's session.
Run local regression checks with:

```sh
node recipes-graphics/jaguar-touch-test/test-jaguar-touch-test.cjs
```

The 22 November 2026 page incorporates Michael's accepted responsiveness fix:
bounded artwork layers, lightweight live-contact overlays when trails are off,
coalesced input redraws, unchanged-label caching and slower diagnostic updates.
Decorative rings pause during touch and resume on release unless explicitly
paused. Native touch, pointer fallback, pinch/pan, trails and contact-test mode
remain available. Long trails remain expensive; this does not promise 60 fps.

Validation covered local regression checks, exact equality with the tested board
page and a local execution of the recipe's install task. A full BitBake image
build was not performed as part of this integration.
