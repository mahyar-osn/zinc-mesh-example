import os

from opencmiss.utils.zinc.field import findOrCreateFieldCoordinates
from opencmiss.zinc.context import Context
from opencmiss.zinc.element import Element
from opencmiss.zinc.field import Field
from opencmiss.zinc.node import Node

from src.zinc_mesh_example.eft_tricubichermite import EftTricubicHermite


class ZincMeshExample(object):

    def __init__(self):
        self._context = Context('Mesh-Example')
        self._region = self._context.getDefaultRegion()

        self._options = {'Use cross derivatives': False,
                         'Number of elements 1': 1,
                         'Number of elements 2': 1,
                         'Number of elements 3': 1
                         }

        self._x = list()
        self._dx_ds1 = list()
        self._dx_ds2 = list()
        self._dx_ds3 = list()
        self._dx_ds12 = list()
        self._dx_ds13 = list()
        self._dx_ds23 = list()
        self._dx_ds123 = list()

    def set_node_parameters(self, node_params):
        for node in range(len(node_params)):
            if not self._options['Use cross derivatives']:
                self._x.extend((node_params[node][0], node_params[node][4], node_params[node][8]))
                self._dx_ds1.extend((node_params[node][1], node_params[node][5], node_params[node][9]))
                self._dx_ds2.extend((node_params[node][2], node_params[node][6], node_params[node][10]))
                self._dx_ds3.extend((node_params[node][3], node_params[node][7], node_params[node][11]))
            if self._options['Use cross derivatives']:
                self._x.extend((node_params[node][0], node_params[node][8], node_params[node][16]))
                self._dx_ds1.extend((node_params[node][1], node_params[node][9], node_params[node][17]))
                self._dx_ds2.extend((node_params[node][2], node_params[node][10], node_params[node][18]))
                self._dx_ds3.extend((node_params[node][3], node_params[node][11], node_params[node][19]))
                self._dx_ds12.extend((node_params[node][4], node_params[node][12], node_params[node][20]))
                self._dx_ds13.extend((node_params[node][5], node_params[node][13], node_params[node][21]))
                self._dx_ds23.extend((node_params[node][6], node_params[node][14], node_params[node][22]))
                self._dx_ds123.extend((node_params[node][7], node_params[node][15], node_params[node][23]))

        return None

    def generate_mesh(self):
        use_cross_derivatives = self._options['Use cross derivatives']
        elements_count1 = self._options['Number of elements 1']
        elements_count2 = self._options['Number of elements 2']
        elements_count3 = self._options['Number of elements 3']

        fm = self._region.getFieldmodule()
        fm.beginChange()
        coordinates = findOrCreateFieldCoordinates(fm)

        nodes = fm.findNodesetByFieldDomainType(Field.DOMAIN_TYPE_NODES)
        node_template = nodes.createNodetemplate()
        node_template.defineField(coordinates)
        node_template.setValueNumberOfVersions(coordinates, -1, Node.VALUE_LABEL_VALUE, 1)
        node_template.setValueNumberOfVersions(coordinates, -1, Node.VALUE_LABEL_D_DS1, 1)
        node_template.setValueNumberOfVersions(coordinates, -1, Node.VALUE_LABEL_D_DS2, 1)
        if use_cross_derivatives:
            node_template.setValueNumberOfVersions(coordinates, -1, Node.VALUE_LABEL_D2_DS1DS2, 1)
        node_template.setValueNumberOfVersions(coordinates, -1, Node.VALUE_LABEL_D_DS3, 1)
        if use_cross_derivatives:
            node_template.setValueNumberOfVersions(coordinates, -1, Node.VALUE_LABEL_D2_DS1DS3, 1)
            node_template.setValueNumberOfVersions(coordinates, -1, Node.VALUE_LABEL_D2_DS2DS3, 1)
            node_template.setValueNumberOfVersions(coordinates, -1, Node.VALUE_LABEL_D3_DS1DS2DS3, 1)

        mesh = fm.findMeshByDimension(3)

        tricubic_hermite = EftTricubicHermite(mesh, use_cross_derivatives)
        eft = tricubic_hermite.create_eft_basic()

        element_template = mesh.createElementtemplate()
        element_template.setElementShapeType(Element.SHAPE_TYPE_CUBE)
        result = element_template.defineField(coordinates, -1, eft)

        cache = fm.createFieldcache()

        # create nodes
        node_identifier = 1
        number_of_nodes = len(self._x) // 3
        for n in range(number_of_nodes):
            node = nodes.createNode(node_identifier, node_template)
            cache.setNode(node)
            coordinates.setNodeParameters(cache, -1, Node.VALUE_LABEL_VALUE, 1, self._x[n*3:(n*3)+3])
            coordinates.setNodeParameters(cache, -1, Node.VALUE_LABEL_D_DS1, 1, self._dx_ds1[n*3:(n*3)+3])
            coordinates.setNodeParameters(cache, -1, Node.VALUE_LABEL_D_DS2, 1, self._dx_ds2[n*3:(n*3)+3])
            coordinates.setNodeParameters(cache, -1, Node.VALUE_LABEL_D_DS3, 1, self._dx_ds3[n*3:(n*3)+3])
            if use_cross_derivatives:
                coordinates.setNodeParameters(cache, -1, Node.VALUE_LABEL_D2_DS1DS2, 1, self._dx_ds12[n*3:(n*3)+3])
                coordinates.setNodeParameters(cache, -1, Node.VALUE_LABEL_D2_DS1DS3, 1, self._dx_ds13[n*3:(n*3)+3])
                coordinates.setNodeParameters(cache, -1, Node.VALUE_LABEL_D2_DS2DS3, 1, self._dx_ds23[n*3:(n*3)+3])
                coordinates.setNodeParameters(cache, -1, Node.VALUE_LABEL_D3_DS1DS2DS3, 1, self._dx_ds123[n*3:(n*3)+3])

            node_identifier = node_identifier + 1

        # create elements
        element_identifier = 1
        no2 = (elements_count1 + 1)
        no3 = (elements_count2 + 1) * no2
        for e3 in range(elements_count3):
            for e2 in range(elements_count2):
                for e1 in range(elements_count1):
                    element = mesh.createElement(element_identifier, element_template)
                    bni = e3 * no3 + e2 * no2 + e1 + 1
                    node_identifiers = [bni, bni + 1, bni + no2, bni + no2 + 1, bni + no3, bni + no3 + 1,
                                        bni + no2 + no3, bni + no2 + no3 + 1]
                    result = element.setNodesByIdentifier(eft, node_identifiers)
                    element_identifier = element_identifier + 1

        fm.defineAllFaces()
        fm.endChange()
        return None

    def write(self, filename):
        self._region.writeFile(filename)


if __name__ == '__main__':
    zinc_mesh = ZincMeshExample()
    nodes = [
        [-2.289980638815949e-01, 4.359194295533442e-01, 8.999804972376069e-01, -3.058680031475802e-03,
         -1.511407546634700e-01, -8.941847677301773e-01, 4.327219253197345e-01, -1.148274205442501e-01,
         2.816184518038198e-01, -1.020188811207134e-01, 5.279052872619872e-02, 9.933807467166211e-01],

        [2.069213656672715e-01, 4.359194295255886e-01, 8.999804972376069e-01, -3.058680031475802e-03,
         -1.045325522391338e+00, -8.941847677856885e-01, 4.327219252919789e-01, -1.148274205720057e-01,
         1.795995706824838e-01, -1.020188811207134e-01, 5.279052872619872e-02, 9.933807467166211e-01],

        [6.709824333617289e-01, 4.359194295533442e-01, 8.999804972376069e-01, -3.058679975964651e-03,
         2.815811706620580e-01, -8.941847677301773e-01, 4.327219253197345e-01, -1.148274205164945e-01,
         3.344089805398314e-01, -1.020188811207134e-01, 5.279052872619872e-02, 9.933807467166211e-01],

        [1.106901862910595e+00, 4.359194295533442e-01, 8.999804971265846e-01, -3.058679975964651e-03,
         -6.126035970658102e-01, -8.941847677301773e-01, 4.327219252919789e-01, -1.148274205720057e-01,
         2.323900994184954e-01, -1.020188811207134e-01, 5.279052874007650e-02, 9.933807467304989e-01],

        [-2.320567438992561e-01, 4.359194295533442e-01, 8.999804972376069e-01, -3.058680017598014e-03,
         -2.659681751954428e-01, -8.941847677301773e-01, 4.327219253197345e-01, -1.148274205164945e-01,
         1.274999198532144e+00, -1.020188811207134e-01, 5.279052872619872e-02, 9.933807466611100e-01],

        [2.038626856496103e-01, 4.359194295255886e-01, 8.999804972376069e-01, -3.058680031475802e-03,
         -1.160152942923311e+00, -8.941847676746661e-01, 4.327219252919789e-01, -1.148274205720057e-01,
         1.172980317410808e+00, -1.020188811207134e-01, 5.279052883722102e-02, 9.933807467721323e-01],

        [6.679237533440678e-01, 4.359194295533442e-01, 8.999804971265846e-01, -3.058679975964651e-03,
         1.667537501300853e-01, -8.941847677301773e-01, 4.327219252919789e-01, -1.148274205164945e-01,
         1.327789727268156e+00, -1.020188811207134e-01, 5.279052872619872e-02, 9.933807467721323e-01],

        [1.103843182892934e+00, 4.359194295533442e-01, 8.999804971265846e-01, -3.058680086986953e-03,
         -7.274310175977829e-01, -8.941847677856885e-01, 4.327219252919789e-01, -1.148274204609834e-01,
         1.225770846146820e+00, -1.020188811207134e-01, 5.279052872619872e-02, 9.933807467721323e-01]
    ]
    zinc_mesh.set_node_parameters(nodes)
    zinc_mesh.generate_mesh()
    zinc_mesh.write(os.path.join(os.path.dirname(__file__), 'test_cube.exf'))
