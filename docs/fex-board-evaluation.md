# FEX ARM64 board evaluation

## Result

On 8 October 2026, FEX-2609 was cross-built and packaged on an approved remote
Yocto runner, then passed the static x86-64 smoke on a physical NXP FRDM-IMX95.
Both recipes passed package QA and generated IPKs; all 879 build tasks succeeded.
The unprivileged trial stopped its private server and removed its fresh scratch
directory after preserving results. The deployed OSTree image was unchanged.
Detailed operational receipts remain private.

This proves startup and this integer/SSE2/syscall fixture on the observed
userspace, not games, Wine, graphics, 32-bit support, performance or production use.

## Opt-in recipes

`fex-emu` builds FEX-2609 at
`395b132f346b1a45def246d10c52245edba1ef02` and eight separately pinned
external repositories. Its headless configuration disables graphics thunks,
Qt GUI, Steam integration, guest-rootfs downloads and offline telemetry.
It installs no binfmt handlers and adds nothing to default images.

The recipe requires ARM64/glibc and meta-clang. Compiler selection is
recipe-local, including a target-class override for machine-level GCC policy;
the GNU C++ runtime is retained. Consumers without meta-clang skip this recipe.
Validate other releases/toolchains independently.

`fex-smoke-test` assembles a static, sectionless x86-64 ELF using `nasm-native`.
It tests an integer loop, SSE2 arithmetic, stdout and exit status without a
guest libc, dynamic loader, cross-linker or downloaded executable. The wrapper
supplies an empty guest rootfs and disables disk cache. Only the deliberately
foreign guest package waives architecture QA; emulator QA remains enabled.
Upstream stripping is patched out so Yocto performs normal debug splitting.
The real unversioned `libFEXCore.so` belongs to the runtime package, not `-dev`.

## Build

Run all Yocto/BitBake/KAS tasks on an approved remote builder, never the local
workstation, including local containers. Use the established FRDM integration
stack with `MACHINE = "imx95-frdm-evk"`, preserving other manifest pins.
Select this distro-layer revision in an evaluation-only manifest or KAS overlay.

First build just the components:

```sh
bitbake fex-emu fex-smoke-test
```

Enable the product feature in the existing product/factory configuration:

```bitbake
DD_PRODUCT_FEATURES:append = " fex"
```

Then build the development image through its existing remote CI flow. Adding
recipes does not flash/update a board, change enrollment, or enroll an
interpreter. Explicit `FEX program` invocation needs no global binfmt handler.

The feature expands to `DISTRO_FEATURES` `fex`, conditionally includes the image
fragment and selects `packagegroup-dd-fex` with the emulator and diagnostic
fixture. ARM64/glibc and meta-clang are validated when selecting the feature.
It stays off by default and does not require a separate Foundries branch.

Remote exact-pin BitBake metadata checks passed with the feature enabled and
disabled. They verified image package selection, packagegroup dependencies,
the recipe-local clang selection, and rejection of unsupported architecture
or missing meta-clang. This focused preflight is not a full image-build proof.

## Verified board and runtime

| Property | Observed value |
| --- | --- |
| Board / machine | NXP FRDM-IMX95 / `imx95-frdm-evk` |
| User | Unprivileged `fio`, UID1000 |
| Image | LmP `5.0.13-3003-96`, target3003 |
| Kernel | `6.12.49-lmp-standard` |
| Host ABI | AArch64, glibc 2.39, 4096-byte pages |
| CPU prerequisites | FP and CRC32 present |
| C++ runtime | Existing `libstdc++.so.6.0.32` |
| Timeout | GNU coreutils 9.4 |

Model, serial, user, image, OSTree, kernel, libc, page size, CPU features and
resources were verified directly before transfer. Shared-board coordination was
context, not authority. No competing NPU/FEX workload was observed.

All seven packaged native ELFs were AArch64 without build-host RPATH/RUNPATH.
The guest was static x86-64. Selected runtime requirements include GLIBC 2.38,
GLIBCXX 3.4.31, CXXABI 1.3.5 and GCC 4.5.0. Live board library definitions
covered them, and the ARM64 loader `--verify` and `--list` succeeded for both
selected native ELFs. Existing system libraries sufficed: no compatibility
library or libc replacement was needed. Package dependency versions and ELF
symbol requirements are distinct; check both for another image.

## Reversible userspace trial

FEX starts/connects to FEXServer even for this static fixture. A client-only
timeout does not contain an automatically detached server. The reviewed trial:

1. Verified a fresh canonical user-owned directory, safe archive members,
   manifest hashes, no symlinks and an empty rootfs.
2. Rejected legacy `~/.fex-emu`, whose upstream precedence can override private
   data paths.
3. Used a byte-identical server copy named `fex-trial-server` and refused normal
   `FEXServer` on its fixed PATH to prevent detached fallback.
4. Set private `FEX_APP_CONFIG_LOCATION`, `FEX_APP_DATA_LOCATION`,
   `FEX_SERVERSOCKETPATH`, `XDG_RUNTIME_DIR`, `FEX_ROOTFS`,
   `FEX_SMOKE_DATADIR` and `FEX_DISKCACHE=0`.
5. Ran `--foreground --wait_pipe 6`; readiness was initialization FIFO EOF,
   not a sleep or guessed success packet.
6. Enclosed server/readiness/guest in GNU `timeout -k 5 30`, disabled core
   dumps and bounded CPU time. Teardown signalled only the captured direct
   child with the exact private executable, then reaped it.
7. Checked no trial executable remained live, rechecked hashes, preserved
   output and removed only the exact directory after ownership/path checks.
   A separate console read confirmed cleanup and unchanged OSTree.

Observed physical-board output:

```text
FEX_TRIAL_PRIVATE_SERVER_READY
FEX x86-64 integer/SSE2/syscall smoke: PASS
FEX_TRIAL_EXIT=0
SSH_SMOKE_EXIT=0
NO_LIVE_TRIAL_PROCESSES
TRIAL_CLEANUP_VERIFIED
```

The server log was empty, readiness returned zero-byte EOF and all six file
hashes matched before/after execution. No board sudo, flash, reboot, system
installation, binfmt enrollment or other-workload kill occurred. FEX was not
left installed.

The installed development-image wrapper is `fex-smoke-test`;
`FEX_SMOKE_DATADIR` can relocate its data. Retain private-server/timeout
supervision for reversible scratch testing. A nonzero exit, missing PASS,
crash or hang is failure.

## Evidence hashes

| Artifact | SHA256 |
| --- | --- |
| Emulator recipe | `040cb8ccb08996d7f77ab65ac3c5315d53aa2182ced510f2e6f8d7f740956318` |
| Smoke recipe | `8c11414e21da5cfc8fd587501967cf325fd47ac9750d8351312ab77db71c152d` |
| Emulator IPK | `1f945d8be97c7c0b85ebe8a8420e80d28108efd3e07a7ba97781978e651d7cff` |
| Smoke IPK | `51ac169856bf740ee2c77465d705d02466703c89aab24a0345fd6831cd5ef355` |
| Tested FEX ELF | `9792302f8421bf6279d07103b90e0b2bd8fe6cd345400c31473357a2c93b73c1` |
| Tested server ELF | `94ca6fcac01a50f7f4f40d8bd320915021b921f6477ad277628f60d8d40ee4c3` |
| Static guest | `0a452bacbbdfe357cc752bc56f4a3eb7dc0d52ebd4a4f8d09b8b04ba177a26ef` |
| Trial manifest | `0ec166e330cea035fba8f5f99c4f256e5939752965f930444d3e5e5efc655e00` |
| Build receipt | `6d30342f301658b2cbf15993ee032466fdc4d744d7099b7bce37ad4d3ccfee7a` |
| Artifact audit receipt | `1bda16e411c490430b08c58c68cdcfd18ae8077ea1ecb6440012653b32287330` |
| Curated board/rollback receipt | `a1c4152cfa1c055c8efed27cb3a1df99df0e26cfa834f34aa9e5dfc446b4746d` |

Build evidence and board execution are separate proof classes. Hashes bind
private receipts; neither manifests nor prepared scripts alone prove a pass.

## Further application work

Dynamically linked x86 programs need a separately provisioned, pinned rootfs
with matching loader/libraries. Record source, licences, checksums and manifests.
FEX is not a sandbox, does not boot x86 kernels and cannot translate x86 kernel
drivers. Use trusted programs on a non-production board without production
credentials. Do not disable memory-ordering emulation to improve benchmarks.

Windows programs require separate Wine/graphics experiments. GPU/USB/ioctl
forwarding is application-specific; graphics thunks are absent here. Such
experiments and any OTA deployment need their own scope and validation.
