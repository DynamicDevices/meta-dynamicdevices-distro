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

The runtime packagegroup uses `TUNE_PKGARCH`, not `all`, because ALSA,
fontconfig and UUID have architecture-dependent Debian package names. Assign
`PACKAGE_ARCH` **before** inheriting `packagegroup`: the class immediately
snapshots it into `PACKAGE_ARCH_EXPANDED`, which selects conditional `allarch`
inheritance. Assigning it afterwards is too late for that decision. This is
confirmed by the [OpenEmbedded class used by the LmP baseline](https://github.com/lmp-mirrors/openembedded-core/blob/7a59dc5ee6edd9596e87c2fbcd1f2594c06b3d1b/meta/classes-recipe/packagegroup.bbclass#L15-L26).
The source regression checks ordering; only the remote build validates actual
BitBake inheritance and dependency-name resolution.

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
