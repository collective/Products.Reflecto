from Acquisition import aq_base


# Called when: removing or adding content from a container, and when using
# cut/paste.
def ReflectorMovedHandler(object, event):
    if object.isTemporary():
        return

    # We can not use checkCreationFlag since the flag is only created
    # during initializeArchetype, while this event is triggered earlier
    # when invokeFactory adds it to the object manager.
    if getattr(aq_base(object), '_at_creation_flag', True):
        return

    indexer = object.restrictedTraverse("@@index")

    if event.oldParent is not None:
        indexer.unindex()
    if event.newParent is not None:
        indexer.index()


def ReflectorModifiedHandler(object, event):
    if object.isTemporary() or object.checkCreationFlag():
        return

    indexer = object.restrictedTraverse("@@index")
    if object.getLife():
        indexer.unindex()
    else:
        indexer.index()

