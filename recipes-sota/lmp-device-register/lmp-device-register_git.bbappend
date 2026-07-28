# Portal bind does NOT belong in public meta-dynamicdevices-distro.
# Set LMP_DEVICE_API / DEVICE_API in the private factory meta-subscriber-overrides.
#
# Lab reference:
#   https://github.com/active-esl/factory-aesl-lab-meta-subscriber-overrides
#   DEVICE_API=https://ota.dynamicdevices.co.uk/v1/devices/
#
# This file intentionally left without LMP_DEVICE_API overrides so SaaS and
# multi-factory builds do not bake a single shared portal URL.
