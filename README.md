# meta-dynamicdevices-distro

## Display-board defaults

Existing Factory Definitions may still select `lmp-dynamicdevices-headless`.
That entry point now routes explicit `display-multimedia` machines to the real
`lmp-dynamicdevices` headed policy and identity. Non-display machines retain
their original legacy configuration byte-for-byte apart from a header comment.
The compatibility route keeps the previous U-Boot 2024.04 preference, timestamp,
DT510 onboarding and Screen's UI bundle. No factory settings need changing.

Build705 passed but remained headless because the old entry point did not load
the product-feature contract. A rootfs-task check now rejects selected display
products missing the actual features, splash payload or console suppression;
source fixture success alone is not image acceptance.

Machines explicitly declaring `MACHINE_FEATURES += "display-multimedia"`
default to `DD_PRODUCT_FEATURES = "display"`: Wayland/Weston, multimedia and
the `display-boot-splash` distro feature. DT510 and Jaguar Screen declare that
capability; inherited EVK `screen` flags and static e-ink do not enable it.
Existing networking, OTA, audit and other selected product features remain.

The boot splash and clean Weston background share AESL artwork. Display-VT
kernel output/gettys are suppressed, but serial diagnostics are retained.
PSplash remains until Weston reports ready; compositor READY is not proof of a
visible desktop frame. The U-Boot-to-Linux hardware reset can still introduce a
blank interval. DT510's build704 U-Boot splash was visibly confirmed on two
warm reboots; this Linux/desktop handover still requires build and bench tests.

Set `DD_DISPLAY_BOOT_SPLASH = "0"` to retain a headed desktop without the new
splash policy. Set `DD_PRODUCT_FEATURES = ""` (or a non-display bundle) for a
headless product; remove any factory-specific forced `display` append too.
For local display-console debugging create `/etc/aesl-enable-display-getty`;
kernel display-console arguments require a separately selected debug image.

Assisted-by: Briar.

**Professional Yocto Distribution Layer for Dynamic Devices Edge Computing Platforms**

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![License: Commercial](https://img.shields.io/badge/License-Commercial-green.svg)](mailto:licensing@dynamicdevices.co.uk)
[![Yocto Compatible](https://img.shields.io/badge/Yocto-scarthgap%20|%20kirkstone-orange.svg)](https://www.yoctoproject.org/)
[![YP Compliance Ready](https://img.shields.io/badge/YP%20Compliance-Distro%20Ready-blue)](https://docs.yoctoproject.org/test-manual/yocto-project-compatible.html)
[![Distro Layer Validation](https://github.com/DynamicDevices/meta-dynamicdevices-distro/actions/workflows/distro-layer-validation.yml/badge.svg)](https://github.com/DynamicDevices/meta-dynamicdevices-distro/actions/workflows/distro-layer-validation.yml)

Distribution layer for Dynamic Devices Edge Computing platforms, providing a
canonical Linux microPlatform (LmP) distribution with composable product
features.

## Overview

This layer provides distribution configurations that extend the standard Linux microPlatform (LmP) with Dynamic Devices-specific features:

- **Security-focused configurations** - Disabled zeroconf, enhanced security policies
- **CRA compliance system** - Automated EU Cyber Resilience Act audit event reporting
- **Device auto-registration** - Automatic device onboarding and management
- **Platform-specific optimizations** - Audio, connectivity, and power management features
- **Commercial license support** - For proprietary components and applications
- **Composable product software** - Headless by default, with explicit Flutter,
  display, audio and Android-container feature bundles

## Documentation & Support

📚 **Comprehensive Documentation**: For detailed documentation, tutorials, and technical guides, visit the [meta-dynamicdevices Wiki](https://github.com/DynamicDevices/meta-dynamicdevices/wiki).

The wiki includes:
- Getting started guides
- Distribution configuration examples
- Build configuration tutorials
- Troubleshooting guides
- Development best practices

## Supported Distributions

New product configurations should use the canonical `lmp-dynamicdevices`
distro and select optional software with `DD_PRODUCT_FEATURES`. See
[`docs/product-feature-architecture.md`](docs/product-feature-architecture.md).

### `lmp-dynamicdevices`
Base distribution with core Dynamic Devices features:
- Security hardening (no zeroconf)
- EU CRA compliance audit system
- Device auto-registration
- Commercial license support
- Platform-specific optimizations

### `lmp-dynamicdevices-base`
Minimal base distribution retained for configurations that need its separate
factory/updater policy.

The old `headless`, `flutter`, `waydroid`, and `headless-waydroid` distro names
are migration-only compatibility inputs. Do not use them for new products.

## Yocto Project Compatibility

This layer is designed to be **Yocto Project Compatible** and follows distribution layer best practices:

- Contains only distribution-specific configurations
- Does not modify builds unless a supported DISTRO is selected
- Passes `yocto-check-layer` validation as a distro layer
- Compatible with Yocto LTS releases (kirkstone, scarthgap)

## Layer Dependencies

- **meta-lmp-base** - Linux microPlatform base layer
- **meta-openembedded** - OpenEmbedded core layers
- **meta-freescale** - NXP/Freescale BSP support

## Usage

### With KAS Build System

```yaml
header:
  version: 14

distro: lmp-dynamicdevices
machine: imx8mm-jaguar-sentai

repos:
  meta-dynamicdevices-distro:
    path: meta-dynamicdevices-distro
```

### Manual Layer Addition

Add to your `conf/bblayers.conf`:

```
BBLAYERS += "${TOPDIR}/../meta-dynamicdevices-distro"
```

Set in your `conf/local.conf`:

```
DISTRO = "lmp-dynamicdevices"
```

## Professional Support

Dynamic Devices provides professional support, consulting, and custom development services for embedded Linux projects.

- **Commercial Support**: Enterprise-grade support with SLAs
- **Custom Development**: Tailored solutions for specific requirements
- **Training & Consulting**: Expert guidance for your development team

Contact: support@dynamicdevices.co.uk

## License

This distribution layer is available under **dual licensing**:

### 🆓 **Open Source License (GPL v3)**
- Free to use for open source projects
- Must comply with GPL v3 copyleft requirements
- Source code modifications must be shared

### 💼 **Commercial License**
- Available for proprietary/commercial use
- No copyleft restrictions
- Custom support and maintenance available
- Contact: licensing@dynamicdevices.co.uk

See the [LICENSE](./LICENSE) file for complete terms and conditions.

## Related Projects

- **[meta-dynamicdevices](https://github.com/DynamicDevices/meta-dynamicdevices)** - Main application layer
- **[meta-dynamicdevices-bsp](https://github.com/DynamicDevices/meta-dynamicdevices-bsp)** - Hardware BSP layer
- **[Wiki](https://github.com/DynamicDevices/meta-dynamicdevices/wiki)** - Comprehensive documentation

---

**Dynamic Devices Ltd** - Professional embedded Linux solutions for edge computing platforms.
