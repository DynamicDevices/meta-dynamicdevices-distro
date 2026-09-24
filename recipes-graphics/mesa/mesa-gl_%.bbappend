# The i.MX BSP already selects mesa-gl for desktop GL while proprietary
# Vivante supplies EGL/GBM/GLES.  For the kiosk, make this same Mesa build own
# the complete API set and enable the Etnaviv/KMSRO Gallium path.
PACKAGECONFIG:append:dd-graphics-etnaviv = " egl gbm gles etnaviv kmsro"
PROVIDES:append:dd-graphics-etnaviv = " virtual/egl virtual/libgbm virtual/libgles1 virtual/libgles2 virtual/libgles3"

# meta-freescale normally makes mesa-gl consume the proprietary EGL provider.
# Mesa is the EGL provider in this configuration, so remove that dependency.
DEPENDS:remove:dd-graphics-etnaviv = "virtual/egl"
RRECOMMENDS:mesa-megadriver:append:class-target:dd-graphics-etnaviv = " libdrm-etnaviv mesa-etnaviv-env"
