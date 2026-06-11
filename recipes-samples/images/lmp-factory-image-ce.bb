SUMMARY = "LMP factory image with CE testing support"
DESCRIPTION = "Specialized factory image with Component Engine testing capabilities for Dynamic Devices platforms"

LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

require recipes-samples/images/lmp-factory-image.bb
require recipes-samples/images/lmp-feature-ce-testing.inc
