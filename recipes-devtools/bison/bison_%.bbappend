# PATCHTOOL=git can refresh Bison's generated-source timestamps during this
# factory build, causing do_compile to regenerate the bison.1 manual page.
# Declare the generator instead of depending on archive timestamp ordering.
DEPENDS:append:class-native = " help2man-native"
