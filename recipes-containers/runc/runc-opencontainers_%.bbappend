# The ai-tools development workspace intentionally uses PATCHTOOL = "git".
# runc carries a nested src/import checkout; Git patch mode sees changes in
# that checkout and refuses to create the top-level patch commit even though
# the recipe patch itself applies only to the top-level tree.  Keep the global
# policy and use quilt only for this recipe in the isolated Cog tuple.
PATCHTOOL:ddkioskcog = "quilt"
