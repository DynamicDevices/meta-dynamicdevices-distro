# The NXP BSP's imxgpu overrides normally remove Mesa EGL/GBM/GLES support.
# Android-container deliberately keeps the NXP BSP but replaces only that
# graphics policy with the upstream DRM/Mesa Etnaviv stack.
# Replace meta-freescale's exact imxgpu removal operations. A more-specific
# empty :remove does not cancel a less-specific deferred removal in BitBake.
PACKAGECONFIG:remove:imxgpu = "${@'' if 'etnaviv' in (d.getVar('DISTRO_FEATURES') or '').split() else 'egl gbm'}"
PACKAGECONFIG:remove:imxgpu3d = "${@'' if 'etnaviv' in (d.getVar('DISTRO_FEATURES') or '').split() else 'gles'}"
PROVIDES:remove:imxgpu = "${@'' if 'etnaviv' in (d.getVar('DISTRO_FEATURES') or '').split() else 'virtual/egl'}"
PROVIDES:remove:imxgpu3d = "${@'' if 'etnaviv' in (d.getVar('DISTRO_FEATURES') or '').split() else 'virtual/libgl virtual/libgles1 virtual/libgles2'}"

PACKAGECONFIG:append:dd-graphics-etnaviv = " egl gbm gles gallium etnaviv kmsro"
RRECOMMENDS:${PN}-megadriver:append:class-target:dd-graphics-etnaviv = " libdrm-etnaviv mesa-etnaviv-env"
