CORE_IMAGE_BASE_INSTALL += " \
    flutter-engine \
    ivi-homescreen \
"

CORE_IMAGE_BASE_INSTALL:append:imx8mm-jaguar-screen = " \
    ivi-homescreen-multi-touch-test \
    screen-flutter-demo \
"
