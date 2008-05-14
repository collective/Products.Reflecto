PROJECTNAME = "Reflecto"

try:
    import Products.CacheSetup
except ImportError:
    HAS_CACHESETUP = False
else:
    HAS_CACHESETUP = True

