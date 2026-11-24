# Optional native Qt 6 runtime

Select `qt6` in `DD_PRODUCT_FEATURES` to install Qt Core/GUI/Widgets/DBus,
Wayland client plugins, ALSA, UUID and fonts. This expands the common
Wayland/OpenGL features globally so Qt's native tools see the same configuration.
The machine must provide `display-multimedia`. Qt remains opt-in regardless of
the machine's existing headed/headless default.

The manifest's shared Qt baseline is meta-qt6 v6.8.2,
`f1563781215bae1e8099637dc18e20601f5c1071`. This feature does not start an
application, replace the browser or change the system compiler/runtime.
It may coexist with kiosk-browser libraries; the display-session owner must
coordinate which application actually runs.

Applications are deployed separately and may remain in a writable home directory.
Do not add vendor payloads, application-specific launchers or private compatibility
libraries to this packagegroup. Any compatibility runtime must remain scoped to
its process, with appropriate provenance, source and notices supplied separately.

Source tests are not BitBake or target acceptance. Before delivery, validate the
exact manifest/distro commits with the authenticated remote factory build,
required review/CI, package manifest, Qt plugin dependencies and ABI checks.
Then test the intended application in its existing display session under separate
device-operation scope. Do not change an enrolled device's update channel merely
to test a development build.

Assisted-by: Briar
