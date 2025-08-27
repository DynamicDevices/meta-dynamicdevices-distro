# Security Policy

## Reporting Security Vulnerabilities

Dynamic Devices takes security seriously. If you discover a security vulnerability in the meta-dynamicdevices-distro layer, please report it responsibly.

### How to Report

**Please DO NOT create public GitHub issues for security vulnerabilities.**

Instead, please report security issues via one of the following methods:

#### Email (Preferred)
- **Security Email**: security@dynamicdevices.co.uk
- **Subject**: `[SECURITY] meta-dynamicdevices-distro: Brief description`

#### Alternative Contact
- **General Contact**: info@dynamicdevices.co.uk
- **Technical Lead**: ajlennon@dynamicdevices.co.uk

### What to Include

When reporting a security vulnerability, please include:

1. **Description** of the vulnerability
2. **Steps to reproduce** the issue
3. **Potential impact** assessment
4. **Affected versions** or commits
5. **Suggested fix** (if available)
6. **Your contact information** for follow-up

### Response Timeline

- **Acknowledgment**: Within 48 hours of receipt
- **Initial Assessment**: Within 5 business days
- **Status Updates**: Weekly until resolution
- **Fix Timeline**: Varies by severity (Critical: 7 days, High: 14 days, Medium: 30 days)

### Severity Levels

- **Critical**: Remote code execution, privilege escalation
- **High**: Local privilege escalation, information disclosure
- **Medium**: Denial of service, minor information leaks
- **Low**: Configuration issues, non-exploitable bugs

### Distribution Security Features

This distro layer implements security-focused configurations:

- **Disabled zeroconf**: Removes Avahi to reduce attack surface
- **Commercial license support**: For security-critical proprietary components
- **Auto-registration**: Secure device onboarding with authentication
- **Improv protocol**: Secure BLE/Serial device provisioning
- **Signing support**: Code signing and verification capabilities
- **Security hardening**: Compiler flags and system hardening options

### Supported Distributions

Security updates are provided for:

- **lmp-dynamicdevices**: Base secure distribution
- **lmp-dynamicdevices-base**: Minimal secure configuration
- **lmp-dynamicdevices-flutter**: Flutter with security features
- **lmp-dynamicdevices-waydroid**: Android container with isolation

### Security Configuration

The distribution layer provides:

- **DISTRO_FEATURES security settings**: Controlled feature enablement
- **Package selection policies**: Security-focused package choices
- **Service configuration**: Secure service defaults
- **Image composition**: Security-hardened image recipes

### Coordinated Disclosure

We follow responsible disclosure practices:

1. **Private Reporting**: Initial report kept confidential
2. **Investigation**: Security team investigates and develops fix
3. **Patch Development**: Fix created and tested
4. **Coordinated Release**: Public disclosure after fix is available
5. **CVE Assignment**: Request CVE if applicable

### Security Resources

- **Yocto Project Security**: https://wiki.yoctoproject.org/wiki/Security
- **Foundries.io LMP Security**: https://docs.foundries.io/latest/reference-manual/security/
- **Linux Security**: https://www.kernel.org/category/security.html

### Contact Information

**Dynamic Devices Ltd**
- Website: https://dynamicdevices.co.uk
- Security Email: security@dynamicdevices.co.uk
- Business Hours: Monday-Friday, 9:00-17:00 GMT

---

*This security policy is effective as of 2024 and may be updated periodically.*
