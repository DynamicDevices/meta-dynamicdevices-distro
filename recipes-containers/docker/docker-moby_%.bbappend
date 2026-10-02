# Docker Moby carries libnetwork as a nested checkout.  With the development
# workspace's global PATCHTOOL = "git", changes below that checkout make the
# top-level patch commit fail even when the recipe patch applied correctly.
# Keep Git globally and use quilt only for Docker in the isolated Cog tuple.
PATCHTOOL:ddkioskcog = "quilt"
