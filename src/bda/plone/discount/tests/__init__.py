from zope.interface import alsoProvides
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import TEST_USER_ID
from plone.app.testing import login
from plone.app.testing import setRoles
from bda.plone.discount.interfaces import IDiscountExtensionLayer


def set_browserlayer(request):
    """Set the BrowserLayer for the request.

    We have to set the browserlayer manually, since importing the profile alone
    doesn't do it in tests.
    """
    alsoProvides(request, IDiscountExtensionLayer)


class DiscountLayer(PloneSandboxLayer):
    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        import bda.plone.discount
        self.loadZCML(package=bda.plone.discount,
                      context=configurationContext)

    def setUpPloneSite(self, portal):
        self.applyProfile(portal, 'bda.plone.discount:default')
        setRoles(portal, TEST_USER_ID, ['Manager'])
        login(portal, TEST_USER_NAME)

    def tearDownZope(self, app):
        pass


Discount_FIXTURE = DiscountLayer()
Discount_INTEGRATION_TESTING = IntegrationTesting(
    bases=(Discount_FIXTURE,),
    name="Discount:Integration")
