PROJECTNAME = "Reflecto"

try:
    import Products.CacheSetup.vocabulary
except ImportError:
    HAS_CACHESETUP = False
else:
    HAS_CACHESETUP = True

