# Chromium kiosk layer adoption (candidate; gate pending)

The first kiosk tuple is `imx8mm-jaguar-screen` with
`DD_PRODUCT_FEATURES = "kiosk-browser"`. The current screen tuple remains
`display flutter godot` and is not modified by this feature selection.

## Candidate inputs

| Layer | Branch | Exact candidate revision | Purpose |
| --- | --- | --- | --- |
| `meta-browser/meta-chromium` | `scarthgap` | `85eeb6b50883d22c977396f5e8fe211a7961cf2e` | `chromium-ozone-wayland` 147.0.7727.116 |
| `meta-lts-mixins` | `scarthgap/rust` | `eedcdc7486ff15c3510c2ceff68c87d9db141312` | Required Rust toolchain mixin |

The Chromium layer declares dependencies on `clang-layer`, `core`,
`openembedded-layer`, and `scarthgap-rust-mixin`. The first three already exist
in the LmP base layer set. Its Scarthgap recipe installs `/usr/bin/chromium`
and requires the `wayland` distro feature. The pinned recipe explicitly sets
`use_ozone=true`, `ozone_platform_wayland=true`, and
`ozone_platform_x11=false`; its default package configuration includes EGL.
These are recipe declarations, not a substitute for rendered hardware proof.

## Static audit so far

`meta-chromium` contains no bbappends or global image/install assignments in
`layer.conf`. Its recipe set includes Chromium, Node.js 22 and native tools.
`meta-lts-mixins` contains a wildcard `rust_%.bbappend`, newer Rust,
`librsvg`, and `libgit2` recipes, and Rust/Cargo classes in `classes-recipe`.
Its `layer.conf` prepends the layer to `BBPATH`, overriding the core classes
for every product. These inputs can alter providers and task graphs
for existing products even when Chromium is not selected. The layer-adoption
gate therefore blocks manifest and BBLAYERS promotion until exact-pinned
baseline comparisons and all maintained image tuples pass. In particular,
compare Rust, Node.js, librsvg and libgit2 providers and versions.

The first exact-pinned kiosk parse completed with 4,207 recipes and zero parse
errors. The Chromium 147.0.7727.116 recipe completed fetch, unpack, and
patch, including its 5.3 GB source archive. Compile and package QA remain
pending. The original screen profile parsed with 4,193 recipes and the same
three warnings as the candidate. An initial shared-manifest experiment changed
21 existing recipe versions: Rust/Cargo variants, Node.js, librsvg, libgit2,
GN and cargo-c. A temporary set of non-kiosk provider pins restored the old
preferred versions, but the mixin's global class override still broke the old
Rust task graph. Those non-kiosk pins have been removed from the proposed
feature contract. Current pins apply only to `kiosk-browser`; the dedicated
manifest branch isolates the mixin from existing products. A fresh baseline
`bitbake -e rust-native` after this change shows `RUSTVERSION="1.75%"`, no
`ddkioskbrowser` override, and no added preferred Node.js or SDK Rust version.
The isolated kiosk stack subsequently parsed with 3,938 recipes and zero
parse errors. Its expanded image environment selects Rust 1.98.1 and Node.js
22.11.0, includes the kiosk package group and Weston, and excludes the
Flutter, Godot, and Waydroid payloads. Its image task graph contains 565
recipe names and 45,218 task edges, with no missing providers or cycles.
This is static build evidence; the exact recipe and image builds are pending.

The baseline `bitbake -g lmp-factory-image` completed with 587 recipe names
and 47,283 task-graph lines. The candidate graph reported **450 unbuildable
tasks** and entered prolonged dependency-loop identification. It was stopped
after nearly 12 minutes with that failure recorded. A smaller
`bitbake -g rust-native` reproduced the loop: the mixin's class override
makes Rust 1.75 native depend on Cargo 1.75 native, while Cargo depends on
Rust. This is an adoption-gate failure despite matching preferred versions.

A separate local copy of the mixin with conditional `BBPATH` precedence
resolved the small `bitbake -g rust-native` graph (33 recipe names, 1,198
task-graph lines). It is an unpinned experiment, so it cannot enter a factory
manifest. The original mixin still breaks the old screen profile if both
layers share one manifest.

The proposed integration instead uses a dedicated local
`main-jaguar-screen-kiosk` manifest branch. It adds exactly pinned
`meta-browser` and `meta-lts-mixins` projects and their two BBLAYERS entries
only on that branch. The existing `main-jaguar-screen` branch retains its
original layer set, avoiding the global class override there. The distro's
Godot bbappend also requires a pinned `meta-godot` layer for parsing. All 26
projects in the kiosk manifest have commit revisions, and the 26 matching local
checkouts were verified. The branch is committed locally but unpublished while
recipe, image, and tuple gates remain open.

A read-only manifest-ref audit found 15 of the 18 existing factory refs
available. Recursive inspection of their XML includes found no `meta-browser`
project. Ten already select older `meta-lts-mixins` Go and Rust projects from
their base manifests; five select no mixin. None selects the candidate kiosk
Rust mixin revision. The refs `imx8mm-jaguar-handheld-5in`,
`imx8mm-jaguar-handheld-7in`, and `main-rpi5` were absent both locally and on
the configured remote. Their maintenance status must be resolved before
claiming the all-tuple gate.

## Required proof before manifest promotion

1. Parse the exact-pinned proposed stack and one kiosk tuple; build the
   Chromium recipe before a complete image.
2. Compare every maintained tuple against its old manifest: selected layers,
   providers, appends, distro features, image packages and task graph.
3. Build every maintained factory and mfgtool/recovery image; classify all
   package and size changes. Keep browser payload out of recovery images.
4. Only then promote the local kiosk manifest branch with its exact layer
   pins and BBLAYERS entries. Record the baseline and candidate manifest SHAs
   and results.

This document records a candidate, not a passed product-readiness gate.
The physical Jaguar Screen target is registered as
`imx8mm-jaguar-screen-2210a09dab86563` in the lab board registry. Its LAN
address is volatile, so board identity must be reconfirmed before testing.
