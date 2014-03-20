import uuid
import plone.api
from datetime import datetime
from zope.interface import implementer
from zope.component import adapter
from node.utils import UNSET
from Products.CMFPlone.interfaces import IPloneSiteRoot
from plone.uuid.interfaces import IUUID
from bda.plone.discount.interfaces import FLOOR_DATETIME
from bda.plone.discount.interfaces import CEILING_DATETIME
from bda.plone.discount.interfaces import CATEGORY_CART_ITEM
from bda.plone.discount.interfaces import CATEGORY_CART
from bda.plone.discount.interfaces import FOR_USER
from bda.plone.discount.interfaces import FOR_GROUP
from bda.plone.discount.interfaces import IDiscountSettings
from bda.plone.discount.interfaces import ICartItemDiscountSettings
from bda.plone.discount.interfaces import IUserCartItemDiscountSettings
from bda.plone.discount.interfaces import IGroupCartItemDiscountSettings
from bda.plone.discount.interfaces import ICartDiscountSettings
from bda.plone.discount.interfaces import IUserCartDiscountSettings
from bda.plone.discount.interfaces import IGroupCartDiscountSettings
from repoze.catalog.catalog import Catalog
from repoze.catalog.indexes.field import CatalogFieldIndex
from repoze.catalog.query import Eq
from repoze.catalog.query import NotEq
from repoze.catalog.query import Ge
from repoze.catalog.query import Le
from souper.interfaces import ICatalogFactory
from souper.soup import NodeAttributeIndexer
from souper.soup import Record
from souper.soup import get_soup


@implementer(ICatalogFactory)
class DiscountRulesCatalogFactory(object):

    def __call__(self, context=None):
        catalog = Catalog()
        # unique id of rule
        uid_indexer = NodeAttributeIndexer('uid')
        catalog[u'uid'] = CatalogFieldIndex(uid_indexer)
        # uid of context rule refers to
        context_uid_indexer = NodeAttributeIndexer('context_uid')
        catalog[u'context_uid'] = CatalogFieldIndex(context_uid_indexer)
        # rule category
        category_indexer = NodeAttributeIndexer('category')
        catalog[u'category'] = CatalogFieldIndex(category_indexer)
        # rule valid from date
        valid_from_indexer = NodeAttributeIndexer('valid_from')
        catalog[u'valid_from'] = CatalogFieldIndex(valid_from_indexer)
        # rule valid to date
        valid_to_indexer = NodeAttributeIndexer('valid_to')
        catalog[u'valid_to'] = CatalogFieldIndex(valid_to_indexer)
        # user this rule applies
        user_indexer = NodeAttributeIndexer('user')
        catalog[u'user'] = CatalogFieldIndex(user_indexer)
        # group this rule applies
        group_indexer = NodeAttributeIndexer('group')
        catalog[u'group'] = CatalogFieldIndex(group_indexer)
        return catalog


@implementer(IDiscountSettings)
class PersistendDiscountSettings(object):
    soup_name = 'bda_plone_discount_rules'
    category = UNSET
    for_attribute = UNSET

    def __init__(self, context):
        self.context = context

    @property
    def rules_soup(self):
        return get_soup(self.soup_name, self.context)

    def rules(self, context, date=None):
        context_uid = uuid.UUID(IUUID(context))
        query = Eq('context_uid', context_uid) & Eq('category', self.category)
        if date is not None:
            query = query & Ge('valid_from', date) & Le('valid_to', date)
        if self.for_attribute == 'user':
            query = query & NotEq('user', UNSET)
        elif self.for_attribute == 'group':
            query = query & NotEq('group', UNSET)
        else:
            query = query & Eq('user', UNSET) & Eq('group', UNSET)
        return self.rules_soup.query(query,
                                     sort_index='valid_from',
                                     reverse=False)

    def delete_rules(self, rules):
        soup = self.rules_soup
        for rule in [_ for _ in rules]:
            del soup[rule]

    def add_rule(self, context, kind, block, value, valid_from,
                 valid_to, user=UNSET, group=UNSET):
        rule = Record()
        rule.attrs['uid'] = uuid.uuid4()
        if self.category is not UNSET:
            assert(isinstance(self.category, str))
        rule.attrs['category'] = self.category
        rule.attrs['context_uid'] = uuid.UUID(IUUID(context))
        rule.attrs['creator'] = plone.api.user.get_current().getId()
        rule.attrs['created'] = datetime.now()
        assert(isinstance(kind, str))
        rule.attrs['kind'] = kind
        assert(isinstance(block, bool))
        rule.attrs['block'] = block
        assert(isinstance(value, float))
        rule.attrs['value'] = value
        if valid_from:
            assert(isinstance(valid_from, datetime))
        else:
            valid_from = FLOOR_DATETIME
        rule.attrs['valid_from'] = valid_from
        if valid_to:
            assert(isinstance(valid_to, datetime))
        else:
            valid_to = CEILING_DATETIME
        rule.attrs['valid_to'] = valid_to
        if user is not UNSET:
            assert(isinstance(user, str))
        rule.attrs['user'] = user
        if group is not UNSET:
            assert(isinstance(group, str))
        rule.attrs['group'] = group
        self.rules_soup.add(rule)


@implementer(ICartItemDiscountSettings)
class CartItemDiscountSettings(PersistendDiscountSettings):
    category = CATEGORY_CART_ITEM


@implementer(IUserCartItemDiscountSettings)
class UserCartItemDiscountSettings(CartItemDiscountSettings):
    for_attribute = FOR_USER


@implementer(IGroupCartItemDiscountSettings)
class GroupCartItemDiscountSettings(CartItemDiscountSettings):
    for_attribute = FOR_GROUP


@implementer(ICartDiscountSettings)
@adapter(IPloneSiteRoot)
class CartDiscountSettings(PersistendDiscountSettings):
    category = CATEGORY_CART


@implementer(IUserCartDiscountSettings)
@adapter(IPloneSiteRoot)
class UserCartDiscountSettings(CartDiscountSettings):
    for_attribute = FOR_USER


@implementer(IGroupCartDiscountSettings)
@adapter(IPloneSiteRoot)
class GroupCartDiscountSettings(CartDiscountSettings):
    for_attribute = FOR_GROUP
