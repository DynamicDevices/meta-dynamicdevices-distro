# The i.MX machine enables the optional proprietary G2D allocator.  The kiosk
# uses DMA heaps with Mesa Etnaviv, so do not pull the galcore-backed provider.
PACKAGECONFIG:remove:dd-graphics-etnaviv = "g2d"
