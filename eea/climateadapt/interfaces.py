from zope.interface import Interface


class IBalticRegionMarker(Interface):
    """ A marker interface for Baltic Region pages. They get a special nav menu
    """


class ITransnationalRegionMarker(Interface):
    """ A marker interface for transnational region pages.
    """
