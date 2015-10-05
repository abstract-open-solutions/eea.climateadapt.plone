""" Importing utils
"""

from plone.dexterity.utils import createContentInContainer
from plone.tiles.interfaces import ITileDataManager
from plone.uuid.interfaces import IUUIDGenerator
from zope.component import getUtility
from zope.pagetemplate.pagetemplatefile import PageTemplateFile
import logging
import lxml.etree
import re

logger = logging.getLogger('eea.climateadapt.importer')
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


def printe(e):
    """ debug function to easily see an etree as pretty printed xml"""
    print lxml.etree.tostring(e, pretty_print=True)


def s2l(text, separator=';'):
    """Converts a string in form: u'EXTREMETEMP;FLOODING;' to a list"""
    return filter(None, text.split(separator))


def parse_settings(text):
    """Changes a string in form:
    # u'sitemap-changefreq=daily\nlayout-template-id=2_columns_iii\nsitemap-include=1\ncolumn-2=56_INSTANCE_9tMz,\ncolumn-1=56_INSTANCE_2cAx,56_INSTANCE_TN6e,\n'
    to a dictionary of settings
    """
    out = {}
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        k, v = line.split('=', 1)
        v = filter(None, v.split(','))
        # if len(v) == 1:
        #     v = v[0]
        out[k] = v
    return out


def solve_dynamic_element(node):

    type_ = node.get('type')

    if type_ == 'image':
        # TODO: don't need to keep this as a list
        imageid = [str(x) for x in node.xpath("dynamic-content/@id")]
        return ('image', None, imageid)

    if type_ == 'text_area':
        return ('text',
                node.get('name'),
                [unicode(x) for x in node.xpath("dynamic-content/text()")]
                )

    if type_ == 'text_box':
        return (
            'dynamic',
            node.get('name'),
            [SOLVERS[child.tag](child) for child in node]
        )

    if type_ == 'text':
        return (
            'dynamic',
            node.get('name'),
            [SOLVERS[child.tag](child) for child in node]
        )

    if type_ in (None, 'list', 'boolean'):
        return (
            type_,
            node.get('name'),
            [SOLVERS[child.tag](child) for child in node]
        )

    raise ValueError("Dynamic element not handled, please write more code")


def solve_dynamic_content(node):
    return node.text
    # return ('text', None, node.text)


def solve_static_content(node):
    return node.text
    # return ('text', None, node.text)


SOLVERS = {
    'dynamic-element': solve_dynamic_element,
    'static-content': solve_static_content,
    'dynamic-content': solve_dynamic_content,
    # 'static-element': solve_static_element,
}


def strip_xml(xmlstr):
    if ("<xml" in xmlstr) or ("<?xml" in xmlstr):
        res = unicode(lxml.etree.fromstring(xmlstr.encode('utf-8')).xpath(
            "*/text()")[0])
    else:
        res = unicode(xmlstr)
    return res


def _clean(s):
    if s == "NULL_VALUE":
        return None
    return s


def _clean_portlet_settings(d):
    _conv = {
        'aceitemtype': 'search_type',
        'anyOfThese': 'special_tags',
        'countries': 'countries',
        'element': 'elements',
        'nrItemsPage': '10',
        'portletSetupTitle_en_GB': 'title',
        'sector': 'sector',
        'sortBy': 'sortBy'
    }
    res = {}
    for k, v in d.items():
        if k not in _conv:
            continue
        res[_conv[k]] = _clean(v)

    return res


def make_aceitem_search_tile(cover, info):
    # Available options
    # title
    # search_text
    # element_type
    # sector
    # special_tags
    # countries

    id = getUtility(IUUIDGenerator)()
    typeName = 'eea.climateadapt.search_acecontent'
    tile = cover.restrictedTraverse('@@%s/%s' % (typeName, id))
    info = _clean_portlet_settings(info)
    ITileDataManager(tile).set(info)

    return {
        'tile-type': typeName,
        'type': 'tile',
        'id': id
    }


def make_aceitem_relevant_content_tile(cover, info):
    id = getUtility(IUUIDGenerator)()
    typeName = 'eea.climateadapt.relevant_acecontent'
    tile = cover.restrictedTraverse('@@%s/%s' % (typeName, id))
    ITileDataManager(tile).set(info)

    return {
        'tile-type': typeName,
        'type': 'tile',
        'id': id
    }

    pass


def make_richtext_tile(cover, content):
    # creates a new tile and saves it in the annotation
    # returns a python objects usable in the layout description
    # content needs to be a dict with keys 'title' and 'text'

    id = getUtility(IUUIDGenerator)()
    typeName = 'collective.cover.richtext'
    tile = cover.restrictedTraverse('@@%s/%s' % (typeName, id))

    content['text'] = unicode(content['text'])
    content['title'] = unicode(content['title'])

    ITileDataManager(tile).set(content)

    return {
        'tile-type': typeName,
        'type': 'tile',
        'id': id
    }


def make_richtext_with_title_tile(cover, content):
    # creates a new tile and saves it in the annotation
    # returns a python objects usable in the layout description
    # content needs to be a dict with keys 'title' and 'text'

    id = getUtility(IUUIDGenerator)()
    typeName = 'eea.climateadapt.richtext_with_title'
    tile = cover.restrictedTraverse('@@%s/%s' % (typeName, id))

    content['text'] = unicode(content['text'])
    content['title'] = unicode(content['title'])

    ITileDataManager(tile).set(content)

    return {
        'tile-type': typeName,
        'type': 'tile',
        'id': id
    }


def make_iframe_embed_tile(cover, url):
    id = getUtility(IUUIDGenerator)()
    type_name = 'collective.cover.embed'
    tile = cover.restrictedTraverse('@@%s/%s' % (type_name, id))

    embed = "<iframe src='%s'></iframe>" % url

    ITileDataManager(tile).set({'title': 'embeded iframe', 'embed': embed})

    return {
        'tile-type': 'collective.cover.embed',
        'type': 'tile',
        'id': id
    }


def get_image(site, imageid):
    repo = site['repository']
    reg = re.compile(str(imageid) + '.[jpg|png]')

    ids = [m.string for m in [reg.match(cid) for cid in repo.contentIds()] if m]

    if len(ids) != 1:
        raise ValueError("Image {} not found in repository".format(imageid))

    return repo[ids[0]]


def make_image_tile(site, cover, info):
    id = getUtility(IUUIDGenerator)()
    type_name = 'collective.cover.banner'
    tile = cover.restrictedTraverse('@@%s/%s' % (type_name, id))

    imageid = info['id']
    image = get_image(site, imageid)
    tile.populate_with_object(image)
    return {
        'tile-type': type_name,
        'type': 'tile',
        'id': id
    }


def make_layout(*rows):
    return rows


def make_row(*cols):
    return {
        'type': 'row',
        'children': cols
    }


def make_column(*groups):
    return groups


# a layout contains rows
# a row can contain columns (in its children).
# a column will contain a group
# a group will have the tile

# sample cover layout. This is a JSON string!
# cover_layout = [
#     {"type": "row", "children":
#      [{"type": "group",
#        "children":
#        [
#            {"tile-type": "collective.cover.richtext", "type": "tile", "id": "be70f93bd1a4479f8a21ee595b001c06"}
#         ],
#        "roles": ["Manager"],
#        "column-size": 8},
#       {"type": "group",
#        "children":
#        [
#            {"tile-type": "collective.cover.embed", "type": "tile", "id": "face16b81f2d46bc959df9da24407d94"}
#        ],
#        "roles": ["Manager"],
#        "column-size": 8}]},
#     {"type": "row",
#      "children":
#         [
#             {"type": "group", "children":
#              [
#                  {"tile-type": "collective.cover.richtext", "type": "tile", "id": "a42d3c2a88c8430da52136e2a204cf25"}
#               ],
#              "roles": ["Manager"],
#              "column-size": 16}]}
# ]


# [{u'children': [{u'children': [None],
#                  'class': 'cell width-2 position-0',
#                  u'column-size': 2,
#                  u'roles': [u'Manager'],
#                  u'type': u'group'},
#                 {u'children': [{u'id': u'36759ad0c8114bb48467b858593b271f',
#                                 u'tile-type': u'collective.cover.richtext',
#                                 u'type': u'tile'}],
#                  'class': 'cell width-14 position-2',
#                  u'column-size': 14,
#                  u'roles': [u'Manager'],
#                  u'type': u'group'}],
#   'class': 'row',
#   u'type': u'row'}]
#


def make_group(size=16, *tiles):
    #{"type": "group", "children":
    #     [
    #         {"tile-type": "collective.cover.richtext", "type": "tile", "id": "a42d3c2a88c8430da52136e2a204cf25"}
    #      ],
    #     "roles": ["Manager"],
    #     "column-size": 16}]

    return {
        'type': 'group',
        'roles': ['Manager'],
        'column-size': size,
        'children': tiles
    }


def noop(*args, **kwargs):
    """ no-op function to help with development of importers.
    It avoids pyflakes errors about not used variables.
    """
    # pprint(args)
    # pprint(kwargs)
    return


def create_cover_at(site, location, id='index_html', **kw):
    parent = site

    for name in [x.strip() for x in location.split('/') if x.strip()]:
        if name not in parent.contentIds():
            parent = createContentInContainer(
                parent,
                'Folder',
                title=name,
            )
        else:
            parent = parent[name]

    cover = createContentInContainer(
        parent,
        'collective.cover.content',
        id=id,
        **kw
    )
    return cover


def log_call(wrapped):
    def wrapper(*args, **kwargs):
        logger.info("Calling %s", wrapped.func_name)
        return wrapped(*args, **kwargs)
    return wrapper


def render(path, options):
    tpl = PageTemplateFile(path, globals())
    ns = tpl.pt_getContext((), options)
    return tpl.pt_render(ns)


def pack_to_table(data):
    """ Convert a flat list of (k, v), (k, v) to a structured list
    """
    visited = []
    rows = []
    acc = []
    for k, v in data:
        if k not in visited:
            visited.append(k)
            acc.append(v)
        else:
            rows.append(acc)
            visited = [k]
            acc = [v]

    rows.append(acc)
    return {'rows': rows, 'cols': visited}


# Search portlet has this info:
#  u'column-5': [(u'filteraceitemportlet_WAR_FilterAceItemportlet_INSTANCE_nY73',
#                 {'aceitemtype': 'NULL_VALUE',
#                  'anyOfThese': 'urban',
#                  'countries': 'NULL_VALUE',
#                  'datainfo_type': '2',
#                  'element': 'NULL_VALUE',
#                  'freetextAny': '2',
#                  'fuzziness': None,
#                  'impact': 'NULL_VALUE',
#                  'nrItemsPage': '10',
#                  'paging': '1',
#                  'portletSetupTitle_en_GB': 'Search results',
#                  'portletSetupTitle_en_US': 'Search results',
#                  'portletSetupUseCustomTitle': 'true',
#                  'sector': 'NULL_VALUE',
#                  'sortBy': 'RATING'})],

# Relevant portlet info (aka listing of content) has this info:
#  u'column-4': [(u'simplefilterportlet_WAR_SimpleFilterportlet_INSTANCE_bZn6',
#                 {'aceitemtype': 'INFORMATIONSOURCE',
#                  'anyOfThese': 'countr-area-urban',
#                  'countries': 'NULL_VALUE',
#                  'datainfo_type': '2',
#                  'element': 'NULL_VALUE',
#                  'freeparameter': '0',
#                  'freetextAny': '2',
#                  'fuzziness': None,
#                  'impact': 'NULL_VALUE',
#                  'lfrWapInitialWindowState': 'NORMAL',
#                  'lfrWapTitle': None,
#                  'nrItemsPage': '7',
#                  'portletSetupCss': '',
#                  'portletSetupShowBorders': 'true',
#                  'portletSetupTitle_en_GB': 'Information Portals',
#                  'portletSetupTitle_en_US': 'Information Portals',
#                  'portletSetupUseCustomTitle': 'true',
#                  'sector': 'NULL_VALUE',
#                  'sortBy': 'RATING'})],


# sortBy is one of:
# set(['NAME', 'NULL_VALUE', 'RATING'])

# impact is always null value

# sector is one of:
# set([None,
#      'AGRICULTURE',
#      'BIODIVERSITY',
#      'COASTAL',
#      'DISASTERRISKREDUCTION',
#      'FINANCIAL',
#      'HEALTH',
#      'INFRASTRUCTURE',
#      'MARINE',
#      'NULL_VALUE',
#      'WATERMANAGEMENT'])

# freeparameter is one of:
# set([None, '0', '1', '2', '3'])

# element is one of :
# set([None, 'MEASUREACTION', 'NULL_VALUE', 'OBSERVATIONS', 'VULNERABILITY'])

# Possible values for anyOfThese:
# set([None,
#      'Ast1-2',
#      'Ast1-3',
#      'Baltic Sea Region',
#      'Baltic sea region policy',
#      'MAPLAYER',
#      'NATP',
#      'NATPCZECHREPUBLIC',
#      'NATPREG',
#      'NATPREG NORTHERN_IRELAND',
#      'NATPREG SCOTLAND',
#      'NATPREG WALES',
#      'SETOFMAPS',
#      'adapt-meas-gen',
#      'agiculture',
#      'agriforestryresource',
#      'ast0-0',
#      'ast0-0city',
#      'ast0-1',
#      'ast0-2',
#      'ast0-3',
#      'ast1-0',
#      'ast1-0b',
#      'ast1-2',
#      'ast1-3',
#      'ast1-4',
#      'ast1-5',
#      'ast2',
#      'ast2-0',
#      'ast2-0city',
#      'ast2-1',
#      'ast2-2',
#      'ast2-3',
#      'ast2-4',
#      'ast2-5',
#      'ast3',
#      'ast3-0',
#      'ast3-2',
#      'ast4',
#      'ast4-0',
#      'ast4-0city',
#      'ast4-1',
#      'ast4-2',
#      'ast4-cbdatabase',
#      'ast5',
#      'ast5-0',
#      'ast5-0city',
#      'ast5-1',
#      'ast6',
#      'ast6-0',
#      'ast6-0city',
#      'ast6-2',
#      'atmosphere',
#      'atmosphereresource',
#      'baltic',
#      'biodiversity',
#      'biodiversityresource',
#      'bsr3-1',
#      'bsr3-2',
#      'bsr3-3',
#      'bsr4-1',
#      'bsr4-2',
#      'bsr4-3',
#      'coastal',
#      'coastalresource',
#      'countr-area-urban',
#      'cryosphereresource',
#      'disaster risk',
#      'disasterresource',
#      'financial',
#      'financialresource',
#      'health',
#      'healthresource',
#      'ice',
#      'infra-res',
#      'infrastructure',
#      'mapset-ast-obsscen',
#      'mapset-ast-vulnrisk',
#      'marineresource',
#      'obs-scen-atm',
#      'obs-scen-cry',
#      'obs-scen-gen',
#      'obs-scen-sea',
#      'obs-scen-ter',
#      'obs-scen-urb',
#      'obs-scen-wat',
#      'org1-global',
#      'org2-europe',
#      'urban',
#      'urbanresource',
#      'vuln-risk-gen',
#      'water',
#      'waterresource'])

# aceitemtype is on of:
# set(['ACTION',
#      'DOCUMENT',
#      'GUIDANCE',
#      'INDICATOR',
#      'INFORMATIONSOURCE',
#      'MAPGRAPHDATASET',
#      'MEASURE',
#      'NULL_VALUE',
#      'ORGANISATION',
#      'TOOL'])
#


# countries is one of:
# set([None,
#      'AT',
#      'BE',
#      'BG',
#      'CH',
#      'CY',
#      'DE',
#      'DK',
#      'EE',
#      'ES',
#      'FI',
#      'FR',
#      'GB',
#      'GR',
#      'HU',
#      'IE',
#      'IS',
#      'IT',
#      'LI',
#      'LT',
#      'LU',
#      'LV',
#      'MT',
#      'NL',
#      'NO',
#      'NULL_VALUE',
#      'PL',
#      'PT',
#      'RO',
#      'SE',
#      'SI',
#      'SK',
#      'TR'])
