# Jaguar touch policy and manual multitouch test

`jaguar-screen-touch` owns the board's identity libinput policy and binds touch
to DSI-1. Jaguar display images include it independently of Flutter. Flutter
depends on the same package rather than owning a duplicate rule. The native
600x1024 coordinate geometry and axis inversion belong to the device tree;
Weston handles output rotation. Do not add compensating scale/reflection in the
application. On 22 November 2026 Michael confirmed the vertical reversal was
resolved after removing the stale `-3.2 0 1 0 1.171875 0` userspace hotfix.

Jaguar kiosk images also include `jaguar-touch-test`, a local HTML diagnostic,
and the `jaguar-touch-test` launcher. It reuses the selected kiosk runtime and
does not replace the configured boot URL or change calibration. The recipe
selects `/usr/bin/${DD_KIOSK_BROWSER_RUNTIME}` (default `dd-kiosk-browser`);
set `DD_KIOSK_TEST_BROWSER` in build configuration for a differently named
provider executable, or override it for a direct test invocation. An existing
Flutter test is also available through `screen-flutter-demo` and
`ivi-homescreen-multi-touch-test`; the browser page avoids needing that separate
application stack for a browser-image bench check.

Run the launcher as the Weston session user. Confirm the visible title is
**Jaguar · multitouch test** and it has ten contact indicators, an active count,
a peak count, and separate Native/Pointer counters. A browser process or an
"Opening in existing browser session" message does not prove it is visible.
Multiple fullscreen windows can leave an earlier page visible. For a bench
session, a temporary final `EnvironmentFile` service drop-in selecting
`DD_KIOSK_URL=file:///usr/share/jaguar-touch-test/index.html`, followed by a
controlled kiosk restart, can select the test while retaining the service's
existing execution context and protections. Remove that specific runtime
drop-in and restart to restore the normal URL; do not disable service hardening.

The page rebuilds native contacts from every TouchEvent's complete `touches`
set, independently of PointerEvents. Single-finger touch starts must make a
mark, and motion must leave trails; no three-finger gesture is required. It
also displays pointer counters and provides a pointer-only fallback. These are
browser events, not raw evdev: the test cannot alone prove where dropped
contacts originate. It never injects touches or claims synthetic tests prove
the physical CTP works.

## Gesture mode

Select **Gesture test**, use `jaguar-touch-test --gestures`, or add
`?mode=gestures` to the page URL. Usage instructions are displayed on the page.
One finger pans the Active-Edge SVG target. Two fingers pinch/spread between 25% and
800% scale; moving their midpoint pans while retaining the image position
under that midpoint. Lifting one finger returns to dragging without jumping.
Additional contacts remain visible but do not replace the two selected fingers.
The page displays scale percentage and pan coordinates; **Reset view** returns
to 100%, **Clear trails** clears contact evidence, and **Contact test** restores
the original marker-only test. Resizing resets the view to a known baseline.

**Show trails / Hide trails** toggles historical marks without hiding live
contact markers, changing gesture state, or clearing the contact count. Trails
start hidden in gesture mode and visible in contact mode; each mode remembers
its own selection for the current page session. Hidden history remains bounded
and can be shown again; **Clear trails** discards it without changing the toggle.

These are application-interpreted touch gestures, not Chromium's native page
zoom or desktop-wide gestures. Browser zoom remains disabled so controls and
diagnostics stay fixed. The page does not change CTP calibration or settings.
Synthetic tests cover pinch anchoring, bounds, pan, contact reordering and
two-to-one transitions; Michael must still check the physical gesture behavior.

The target embeds the canonical
`marketing-collateral/brand/lockups/active-edge-symbol-wordmark-lockup.svg`
(SHA-256 `d416b2373a56270fc1027c9ff4f2d9770a2c81f61ce1a605c7844f5eef95be26`).
Its five path elements are retained verbatim; animation is on surrounding
signal rings, not a redrawn or morphed logo. The previous white checkerboard
rectangle is removed. **Pause animation** freezes the rings without disabling
pinch/pan; **Play animation** resumes them. Reduced-motion preference starts
paused. The main screen-edge border remains for alignment checks.
The package is marked CLOSED because it now contains brand assets; this does
not offer rights in Active-Edge marks under the code's earlier MIT metadata.

Manual acceptance:

1. Clear trails. Move one finger: expect one indicator, marker and trail.
2. Keep it down and add another: expect two independently moving contacts.
3. Add fingers progressively (three, then five); compare active and peak counts.
4. Lift fingers individually and then all: active must return to zero.
5. Test all corners and edges. Report Native and Pointer counters if a contact
   is missing or only three fingers seem to work. Ten advertised kernel slots
   do not establish ten physically verified contacts.

Regression checks: `node scripts/test-jaguar-touch-test.mjs` and
`node recipes-graphics/jaguar-touch-test/test-jaguar-touch-test.cjs`.
Also build `jaguar-screen-touch jaguar-touch-test` in the actual Yocto workspace,
check their inclusion in the resulting Jaguar image, and repeat physical tests.
Local source and JS tests are not a built/released image or OTA acceptance.

(Briar helped draft this)
