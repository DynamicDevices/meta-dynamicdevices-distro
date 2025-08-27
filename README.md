# meta-dynamicdevices-distro

**Professional Yocto Distribution Layer for Dynamic Devices Edge Computing Platforms**

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![License: Commercial](https://img.shields.io/badge/License-Commercial-green.svg)](mailto:licensing@dynamicdevices.co.uk)
[![Yocto Compatible](https://img.shields.io/badge/Yocto-scarthgap%20|%20kirkstone-orange.svg)](https://www.yoctoproject.org/)
[![YP Compatible](https://img.shields.io/badge/YP%20Compatible-Distro%20Layer%20✓-brightgreen)](https://docs.yoctoproject.org/test-manual/yocto-project-compatible.html)
[![Layer Validation](https://github.com/DynamicDevices/meta-dynamicdevices/actions/workflows/yocto-layer-validation.yml/badge.svg)](https://github.com/DynamicDevices/meta-dynamicdevices/actions/workflows/yocto-layer-validation.yml)

Distribution layer for Dynamic Devices Edge Computing platforms, providing custom Linux microPlatform (LmP) distributions with specialized features and configurations.

## Overview

This layer provides distribution configurations that extend the standard Linux microPlatform (LmP) with Dynamic Devices-specific features:

- **Security-focused configurations** - Disabled zeroconf, enhanced security policies
- **Device auto-registration** - Automatic device onboarding and management
- **Platform-specific optimizations** - Audio, connectivity, and power management features
- **Commercial license support** - For proprietary components and applications
- **Multiple distribution variants** - Base, Flutter, Waydroid configurations

## Documentation & Support

📚 **Comprehensive Documentation**: For detailed documentation, tutorials, and technical guides, visit the [meta-dynamicdevices Wiki](https://github.com/DynamicDevices/meta-dynamicdevices/wiki).

The wiki includes:
- Getting started guides
- Distribution configuration examples
- Build configuration tutorials
- Troubleshooting guides
- Development best practices

## Supported Distributions

### `lmp-dynamicdevices`
Base distribution with core Dynamic Devices features:
- Security hardening (no zeroconf)
- Device auto-registration
- Commercial license support
- Platform-specific optimizations

### `lmp-dynamicdevices-base`
Minimal base distribution for embedded applications

### `lmp-dynamicdevices-flutter`
Distribution with Flutter/Dart runtime support for modern UI applications

### `lmp-dynamicdevices-waydroid`
Distribution with Android container support via Waydroid

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
