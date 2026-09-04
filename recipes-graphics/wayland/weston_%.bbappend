# The NXP machine override enables the proprietary G2D renderer. Etnaviv uses
# Weston's normal GL renderer and must not pull virtual/libg2d/libgal-imx.
PACKAGECONFIG_G2D:dd-graphics-etnaviv = ""
PACKAGECONFIG:remove:dd-graphics-etnaviv = "imxg2d"
