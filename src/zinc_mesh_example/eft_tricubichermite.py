from opencmiss.zinc.element import Elementbasis


class EftTricubicHermite:
    """Factory class for creating element field templates for a 3-D mesh using tricubic Hermite basis.
    """

    def __init__(self, mesh, use_cross_derivatives):
        """
        :param mesh:  Zinc mesh to create element field templates in.
        :param use_cross_derivatives: Set to True if you want cross derivative terms.
        """
        assert mesh.getDimension() == 3, 'EftTricubicHermite: not a 3-D Zinc mesh'
        self._mesh = mesh
        self._use_cross_derivatives = use_cross_derivatives
        self._fm = mesh.getFieldmodule()
        self._tricubic_hermite_basis = self._fm.createElementbasis(3, Elementbasis.FUNCTION_TYPE_CUBIC_HERMITE)

    def create_eft_basic(self):
        """
        Create the basic tricubic hermite element field template with 1:1 mappings to
        node derivatives, with or without cross derivatives.
        :return: Element field template
        """
        if not self._use_cross_derivatives:
            return self.create_eft_no_cross_derivatives()
        eft = self._mesh.createElementfieldtemplate(self._tricubic_hermite_basis)
        assert eft.validate(), 'EftTricubicHermite.createEftBasic:  Failed to validate eft'
        return eft

    def create_eft_no_cross_derivatives(self):
        """
        Create a basic tricubic hermite element field template with 1:1 mappings to
        node derivatives, without cross derivatives.
        :return: Element field template
        """
        eft = self._mesh.createElementfieldtemplate(self._tricubic_hermite_basis)
        for n in range(8):
            eft.setFunctionNumberOfTerms(n*8 + 4, 0)
            eft.setFunctionNumberOfTerms(n*8 + 6, 0)
            eft.setFunctionNumberOfTerms(n*8 + 7, 0)
            eft.setFunctionNumberOfTerms(n*8 + 8, 0)
        assert eft.validate(), 'EftTricubicHermite.createEftNoCrossDerivatives:  Failed to validate eft'
        return eft
