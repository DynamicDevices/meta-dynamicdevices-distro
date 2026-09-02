CORE_IMAGE_BASE_INSTALL += " \
    packagegroup-dd-flutter \
"

CORE_IMAGE_BASE_INSTALL:append:imx8mm-jaguar-screen = " \
    ivi-homescreen-multi-touch-test \
    screen-flutter-demo \
"
