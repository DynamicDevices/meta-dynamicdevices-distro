# Chromium toolchain decision

Date: 1st October 2026

## Decision

Keep Chromium 147 on the Clang toolchain selected by `meta-browser`.

This selection is recipe-local. Enabling the kiosk browser does not switch the
whole distribution from GCC to Clang. Other recipes continue to use the distro
toolchain unless they explicitly select another compiler.

The production work is therefore to make the Foundries Clang build complete
reliably. GCC remains useful only as an isolated diagnostic experiment; it is
not the intended kiosk production configuration.

## Evidence

Foundries target 2999 compiled Chromium with Clang to approximately task
42313 of 60361. The retained console log contains no compiler diagnostic or
Ninja source failure. It repeatedly reports that the command seemed hung and
then terminates after a very long elapsed build, so the evidence points to the
build/watchdog path rather than a demonstrated Clang compilation defect.

The GCC experiment on ai-tools proved the following:

- BitBake selected GCC/G++ for Chromium's host and AArch64 target toolchains.
- Chromium's GN configuration completed successfully.
- GN generated GCC compile, archive and link commands with `is_clang=false`.
- Real compilation then failed immediately in Chromium 147's bundled libc++
  headers because they use Clang compiler built-ins that GCC does not provide.

Making GCC viable would require a maintained downstream Chromium/libc++
compatibility patch set. That cost is not justified while Clang is Chromium's
supported upstream toolchain and the observed Foundries failure is not a Clang
compiler error.

## Next engineering focus

1. Retain Clang only for the Chromium recipe and its recipe-local host tools.
2. Preserve the existing 32-job, 32-CPU and 48 GB Foundries resource gate.
3. Diagnose the Foundries command watchdog and maximum task/runtime behaviour.
4. Improve Chromium sstate/cache reuse so unchanged compiler work is not lost.
5. Re-run the exact Clang build once the worker/watchdog path is corrected.

Do not promote the GCC experiment into the manifest or release branch without
a new explicit decision supported by a complete compile and runtime proof.
