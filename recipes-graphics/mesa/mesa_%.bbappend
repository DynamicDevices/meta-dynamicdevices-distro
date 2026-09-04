# The NXP BSP's imxgpu overrides normally remove Mesa EGL/GBM/GLES support.
# Android-container deliberately keeps the NXP BSP but replaces only that
# graphics policy with the upstream DRM/Mesa Etnaviv stack.
PACKAGECONFIG:append:dd-graphics-etnaviv = " egl gbm gles gallium etnaviv kmsro"
RRECOMMENDS:${PN}-megadriver:append:class-target:dd-graphics-etnaviv = " libdrm-etnaviv mesa-etnaviv-env"
