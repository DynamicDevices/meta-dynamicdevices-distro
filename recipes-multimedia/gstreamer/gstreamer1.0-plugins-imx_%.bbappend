# Preserve the NXP VPU plugins but remove their optional galcore/G2D path when
# the Android product selects Mesa Etnaviv.
PACKAGECONFIG:remove:dd-graphics-etnaviv = "g2d"
DEPENDS:remove:dd-graphics-etnaviv = "virtual/libg2d libgal-imx"
