from Products.Five.browser import BrowserView
from collective.cover.browser.cover import Standard
from eea.climateadapt.vocabulary import ace_countries_dict
from zExceptions import NotFound
import json
import re


labels = """
acesearch-geochars-lbl-GLOBAL=Global
acesearch-geochars-lbl-EUROPE=Europe
acesearch-geochars-lbl-MACRO_TRANSNATIONAL_REGION=Macro-Transnational Regions
acesearch-geochars-lbl-BIOGRAPHICAL_REGION=Biogeographical Regions
acesearch-geochars-lbl-COUNTRIES=Countries
acesearch-geochars-lbl-SUBNATIONAL=Subnational Regions
acesearch-geochars-lbl-CITY=Municipality Name
acesearch-geochars-lbl-TRANS_MACRO_NORTHPERI=Northern Periphery
acesearch-geochars-lbl-TRANS_MACRO_BACLITC=Baltic Sea
acesearch-geochars-lbl-TRANS_MACRO_NW_EUROPE=North West Europe
acesearch-geochars-lbl-TRANS_MACRO_N_SEA=North Sea
acesearch-geochars-lbl-TRANS_MACRO_ATL_AREA=Atlantic Area
acesearch-geochars-lbl-TRANS_MACRO_ALP_SPACE=Alpine Space
acesearch-geochars-lbl-TRANS_MACRO_CEN_EUR=Central Europe
acesearch-geochars-lbl-TRANS_MACRO_SW_EUR=South West Europe
acesearch-geochars-lbl-TRANS_MACRO_MED=Mediterranean
acesearch-geochars-lbl-TRANS_MACRO_SE_EUR=South East Europe
acesearch-geochars-lbl-TRANS_MACRO_CAR_AREA=Caribbean Area
acesearch-geochars-lbl-TRANS_MACRO_MACRONESIA=Macronesia
acesearch-geochars-lbl-TRANS_MACRO_IND_OCEAN_AREA=Indian Ocean Area
acesearch-geochars-lbl-TRANS_BIO_ALPINE=Alpine
acesearch-geochars-lbl-TRANS_BIO_ATLANTIC=Atlantic
acesearch-geochars-lbl-TRANS_BIO_ARCTIC=Arctic
acesearch-geochars-lbl-TRANS_BIO_CONTINENTAL=Continental
acesearch-geochars-lbl-TRANS_BIO_MEDIT=Mediterranean
acesearch-geochars-lbl-TRANS_BIO_PANONIAN=Panonian
"""

TRANSLATED = {}

for line in filter(None, labels.split('\n')):
    first, label = line.split('=')
    name = first.split('-lbl-')[1]
    TRANSLATED[name] = label


class AceViewApi(object):

    def _render_geochar_element(self, value):
        value = TRANSLATED[value]
        if value == 'Global':
            return value + u"<br/>"
        else:
            return value + u":<br/>"

    def _render_geochar_macrotrans(self, value):
        tpl = u"<p>Macro-Transnational region: <br/>{0}</p>"
        return tpl.format(u", ".join([TRANSLATED[x] for x in value]))

    def _render_geochar_biotrans(self, value):
        return u" ".join(TRANSLATED.get(x, x) for x in value)

    def _render_geochar_countries(self, value):
        tpl = u"<p>Countries:<br/>{0}</p>"
        return tpl.format(u", ".join(self.get_countries(value)))

    def _render_geochar_subnational(self, value):
        tpl = "<p>Sub Nationals: <br/>{0}"
        # a list like: ['SUBN_Marche__IT_']

        out = []
        for line in value:
            n_c = line[3:]
            reg, country = re.findall('_.+?_', n_c)
            t = "{0} ({1})".format(reg[1:-1], country[1:-1])
            out.append(t)

        text = "<br/>".join(out)
        return tpl.format(text)

    def _render_geochar_city(self, value):
        text = value
        if isinstance(value, (list, tuple)):
            text = u" ".join(value)
        return u"<p>City: {0}</p>".format(text)

    def render_geochar(self, value):
        # value is a mapping such as:
        # u'{"geoElements":{"element":"EUROPE",
        #                   "macrotrans":["TRANS_MACRO_ALP_SPACE"],
        #                   "biotrans":[],
        #                   "countries":[],
        #                   "subnational":[],
        #                   "city":""}}'

        if not value:
            return u""

        value = json.loads(value)

        out = []
        order = ['element', 'macrotrans', 'biotrans',
                 'countries', 'subnational', 'city']

        for key in order:
            element = value['geoElements'].get(key)
            if element:
                renderer = getattr(self, "_render_geochar_" + key)
                out.append(renderer(element))

        return u" ".join(out)

    def link_to_original(self):
        """ Returns link to original object, to allow easy comparison
        """
        site = "http://climate-adapt.eea.europa.eu"
        if hasattr(self.context, '_aceitem_id'):
            return ("{0}/viewaceitem?aceitem_id={1}".format(
                site, self.context._aceitem_id))
        if hasattr(self.context, '_acemeasure_id'):
            return ("{0}/viewmeasure?ace_measure_id={1}".format(
                site, self.context._acemeasure_id))
        if hasattr(self.context, '_aceproject_id'):
            return (
                "{0}/projects1?ace_project_id={1}".format(
                    site, self.context._aceproject_id))

    def get_countries(self, country_list):
        return [ace_countries_dict.get(x, x) for x in country_list]


class Navbar(BrowserView):
    """ The global site navbar
    """

    _menu = """
        About        /about

        Search the database         /data-and-downloads

        EU policy                          /eu-adaptation-policy
            EU Adaptation Strategy         /eu-adaptation-policy/strategy
            EU mainstreaming in sector policies   /eu-adaptation-policy/mainstreaming
            EU funding of adaptation       /eu-adaptation-policy/funding
            Mayors Adapt                   /mayors-adapt
                -Mayors Adapt               /mayors-adapt
                -Register your City         /mayors-adapt/register
                -City Profiles              /city-profile

        Countries, regions, cities         /countries-regions
            Transnational regions          /transnational-regions
            Cities and towns               /cities
            Country Information            /countries

        Knowledge               /knowledge
            Adaptation information         /adaptation-information/general
                -Adaptation information         /adaptation-information/general
                -Observations and scenarios    /observations-and-scenarios
                -Vulnerabilities and risks     /vulnerabilities-and-risks
                -Adaptation options            /adaptation-measures
                -Adaptation strategies         /adaptation-strategies
                -Research projects             /research-projects
            Tools                          /tools/general
                -Tools                         /tools/general
                -Adaptation Support Tool       /adaptation-support-tool
                -Case study search tool        /sat
                -Uncertainty guidance          /uncertainty-guidance
                -Map viewer                    /tools/map-viewer
                -Urban adaptation support tool    /tools/urban-ast/step-0-0
                -Urban vulnerability Map book     /tools/urban-adaptation/introduction
                -Guidelines for project managers  /guidelines-for-project-managers
                -Time series tool                 /tools/time-series-tool
                -Additional Tools                 /additional-tools
                -General                          /general

        Network                 /network
            Organisations           /organisations
            Global Platforms        /international

        Help                        /help
    """

    def menu(self):
        lines = self._menu.split('\n')
        sections = []
        this_section = None
        for line in lines:
            line = line.strip()

            # empty lines at beginning of docstring
            if not line and this_section is None:
                continue

            # new section
            if not line and this_section:
                sections.append(this_section)
                this_section = None
                continue

            # new section
            if line and this_section is None:
                lpos = line.find('/')
                label, link = line[:lpos].strip(), line[lpos:].strip()
                this_section = [label, link, []]
                continue

            # link inside section
            if line and this_section and line[0] != '-':
                lpos = line.find('/')
                label, link = line[:lpos].strip(), line[lpos:].strip()
                this_section[2].append((label, link, []))
                continue

            # link inside subsection
            if line and this_section and line[0] == '-':
                lpos = line.find('/')
                label, link = line[1:lpos].strip(), line[lpos:].strip()
                this_section[2][-1][2].append((label, link))

        if this_section:
            sections.append(this_section)

        return sections


#    def menu(self):
#        lines = self._menu.split('\n')
#        sections = []
#        this_section = None
#        for line in lines:
#            line = line.strip()

#            # empty lines at beginning of docstring
#            if not line and this_section is None:
#                continue

#            # new section
#            if not line and this_section:
#                sections.append(this_section)
#                this_section = None
#                continue

#            # new section
#            if line and this_section is None:
#                lpos = line.find('/')
#                label, link = line[:lpos].strip(), line[lpos:].strip()
#                this_section = [label, link, []]
#                continue

#            # link inside section
#            if line and this_section:
#                lpos = line.find('/')
#                label, link = line[:lpos].strip(), line[lpos:].strip()
#                this_section[2].append((label, link))

#        if this_section:
#            sections.append(this_section)

#        return sections


class ViewAceItem(BrowserView):
    """
    """

    def __call__(self, REQUEST):

        aceitem_id = REQUEST.get('aceitem_id')
        if aceitem_id:
            try:
                aceitem_id = int(aceitem_id)
            except ValueError:
                raise NotFound
        else:
            raise NotFound

        return redirect(self.context, REQUEST, 'aceitem_id', aceitem_id)


class ViewAceMeasure(BrowserView):
    """
    """

    def __call__(self, REQUEST):

        acemeasure_id = REQUEST.get('ace_measure_id')
        if acemeasure_id:
            try:
                acemeasure_id = int(acemeasure_id)
            except ValueError:
                raise NotFound
        else:
            raise NotFound

        return redirect(self.context, REQUEST, 'acemeasure_id', acemeasure_id)


class ViewAceProject(BrowserView):
    """
    """

    def __call__(self, REQUEST):

        aceproject_id = REQUEST.get('ace_project_id')
        if aceproject_id:
            try:
                aceproject_id = int(aceproject_id)
            except ValueError:
                raise NotFound
        else:
            raise NotFound

        return redirect(self.context, REQUEST, 'aceproject_id', aceproject_id)


def redirect(site, REQUEST, key, itemid):
    portal_catalog = site.portal_catalog
    brains = portal_catalog({key: itemid})
    if not brains:
        raise NotFound
    ob = brains[0].getObject()
    return REQUEST.RESPONSE.redirect(ob.absolute_url(), status=301)


class CoverNoTitleView(Standard):
    """
    """

    def __call__(self):
        return self.index()


