# The Screen image is Wayland-only. mesa-demos can build its EGL/Wayland
# utilities without X11, so relax the upstream recipe's overly broad gate.
REQUIRED_DISTRO_FEATURES:imx8mm-jaguar-screen = "opengl wayland"

PACKAGECONFIG:imx8mm-jaguar-screen = "drm egl gles1 gles2 wayland"
