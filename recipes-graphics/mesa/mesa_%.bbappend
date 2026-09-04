# The NXP BSP's imxgpu overrides normally remove Mesa EGL/GBM/GLES support.
# Android-container deliberately keeps the NXP BSP but replaces only that
# graphics policy with the upstream DRM/Mesa Etnaviv stack.
PACKAGECONFIG:remove:imxgpu:dd-graphics-etnaviv = ""
PACKAGECONFIG:remove:imxgpu3d:dd-graphics-etnaviv = ""
PROVIDES:remove:imxgpu:dd-graphics-etnaviv = ""
PROVIDES:remove:imxgpu3d:dd-graphics-etnaviv = ""

PACKAGECONFIG:append:dd-graphics-etnaviv = " egl gbm gles gallium etnaviv kmsro"
RRECOMMENDS:${PN}-megadriver:append:dd-graphics-etnaviv = " libdrm-etnaviv mesa-etnaviv-env"
