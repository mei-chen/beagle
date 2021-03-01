from django.test import TestCase
from marketing.helpers import ShoppingCart, ShoppingCartItem, ShoppingCartInvalidQuantityException
from marketing.subscriptions import Subscription
from marketing.models import Coupon


class SomeSubscription(Subscription):
    __abstract__ = False
    uid = "Some"
    name = "This Subscription"
    description = "This description"
    price = 10.99


class AnotherSubscription(Subscription):
    __abstract__ = False
    uid = "Another"
    name = "Another Subscription"
    description = "Another description"
    price = 20.00


class YetAnotherSubscription(Subscription):
    __abstract__ = False
    uid = "YetAnother"
    name = "Yet Another Subscription"
    description = "Yet Another description"
    price = 12.00


class ShoppingCartTestCase(TestCase):
    def test_item(self):
        item = ShoppingCartItem(SomeSubscription, 3)
        self.assertEqual(item.total_price, 32.97)

    def test_0_items(self):
        item = ShoppingCartItem(SomeSubscription, 0)
        self.assertEqual(item.total_price, 0)

    def test_negative_items(self):
        self.assertRaises(ShoppingCartInvalidQuantityException, ShoppingCartItem, SomeSubscription, -2)

    def test_item_repr(self):
        item = ShoppingCartItem(SomeSubscription, 0)
        self.assertEqual(repr(item), "(<Subscription This Subscription (This description)>, 0)")

    def test_item_str(self):
        item = ShoppingCartItem(SomeSubscription, 0)
        self.assertEqual(str(item), "Item=This Subscription - [USD10.99] (This description), Quantity=0, Total=0.0")

    def test_item_serialize(self):
        item = ShoppingCartItem(SomeSubscription, 3)
        self.assertEqual(item.serialize(), {'coupon': None, 'quantity': 3, 'uid': 'Some'})

    def test_item_serialize_with_coupon(self):
        coupon = Coupon(title="Awesome offer!!!",
                        code='12341234',
                        subscription=SomeSubscription.uid,
                        special_price=5.25)

        item = ShoppingCartItem(SomeSubscription, 3)
        item.apply_coupon(coupon)
        self.assertEqual(item.serialize(), {'coupon': '12341234', 'quantity': 3, 'uid': 'Some'})

    def test_item_unserialize(self):
        item = ShoppingCartItem.unserialize({'quantity': 3, 'uid': 'Some'})
        self.assertEqual(item.coupon, None)
        self.assertEqual(item.quantity, 3)
        self.assertEqual(item.item, SomeSubscription)

    def test_item_unserialize_with_coupon(self):
        coupon = Coupon(title="Awesome offer!!!",
                        code='12341234',
                        subscription=SomeSubscription.uid,
                        special_price=5.25)
        coupon.save()

        item = ShoppingCartItem.unserialize({'coupon': '12341234', 'quantity': 3, 'uid': 'Some'})
        self.assertEqual(item.coupon, coupon)
        self.assertEqual(item.quantity, 3)
        self.assertEqual(item.item, SomeSubscription)

    def test_item_apply_coupon(self):
        coupon = Coupon(title="Awesome offer!!!",
                        code='12341234',
                        subscription=SomeSubscription.uid,
                        special_price=5.25)

        item = ShoppingCartItem(SomeSubscription, 3)
        self.assertEqual(item.total_price, 32.97)
        self.assertTrue(item.coupon_applies(coupon))
        item.apply_coupon(coupon)
        self.assertEqual(item.total_price, 15.75)

    def test_item_apply_coupon_percentage(self):
        coupon = Coupon(title="Awesome offer!!!",
                        code='12341234',
                        subscription=SomeSubscription.uid,
                        discount_percent=90.0)

        item = ShoppingCartItem(SomeSubscription, 3)
        self.assertEqual(item.total_price, 32.97)
        self.assertTrue(item.coupon_applies(coupon))
        item.apply_coupon(coupon)
        self.assertEqual(item.total_price, 3.3)

    def test_shopping_cart(self):
        cart = ShoppingCart()
        cart.add(SomeSubscription, 1)

        self.assertEqual(cart.total_price, 10.99)
        self.assertEqual(cart.total_count, 1)
        self.assertEqual(cart.distinct_count, 1)

    def test_shopping_cart_multiple_items(self):
        cart = ShoppingCart()
        cart.add(SomeSubscription, 1)
        cart.add(AnotherSubscription, 12)
        cart.add(YetAnotherSubscription, 2)

        self.assertEqual(cart.total_price, 274.99)
        self.assertEqual(cart.total_count, 15)
        self.assertEqual(cart.distinct_count, 3)

    def test_shopping_cart_multiple_identical_items(self):
        cart = ShoppingCart()
        cart.add(SomeSubscription, 1)
        cart.add(SomeSubscription, 12)
        cart.add(SomeSubscription, 2)

        self.assertEqual(cart.total_price, 164.85)
        self.assertEqual(cart.total_count, 15)
        self.assertEqual(cart.distinct_count, 1)

    def test_shopping_cart_coupon(self):
        cart = ShoppingCart()
        cart.add(SomeSubscription, 1)
        cart.add(AnotherSubscription, 12)
        cart.add(YetAnotherSubscription, 2)

        coupon = Coupon(title="Awesome offer!!!",
                        code='12341234',
                        subscription=SomeSubscription.uid,
                        discount_percent=90.0)

        cart.apply_coupon(coupon)

        self.assertEqual(cart.total_price, 265.1)
        self.assertEqual(cart.total_count, 15)
        self.assertEqual(cart.distinct_count, 3)

    def test_shopping_cart_getter(self):
        cart = ShoppingCart()
        cart.add(SomeSubscription, 1)
        cart.add(AnotherSubscription, 12)
        cart.add(YetAnotherSubscription, 2)

        coupon = Coupon(title="Awesome offer!!!",
                        code='12341234',
                        subscription=SomeSubscription.uid,
                        discount_percent=90.0)

        cart.apply_coupon(coupon)

        self.assertEqual(len(cart), 3)
        self.assertEqual(cart[0].item, SomeSubscription)
        self.assertEqual(cart[1].item, AnotherSubscription)
        self.assertEqual(cart[2].item, YetAnotherSubscription)

        self.assertEqual(cart[SomeSubscription].quantity, 1)
        self.assertEqual(cart[AnotherSubscription].quantity, 12)
        self.assertEqual(cart[YetAnotherSubscription].quantity, 2)

        self.assertEqual(cart[SomeSubscription.uid].quantity, 1)
        self.assertEqual(cart[AnotherSubscription.uid].quantity, 12)
        self.assertEqual(cart[YetAnotherSubscription.uid].quantity, 2)

    def test_shopping_cart_serialize(self):
        cart = ShoppingCart()
        cart.add(SomeSubscription, 1)
        cart.add(AnotherSubscription, 12)
        cart.add(YetAnotherSubscription, 2)

        coupon = Coupon(title="Awesome offer!!!",
                        code='12341234',
                        subscription=SomeSubscription.uid,
                        discount_percent=90.0)

        cart.apply_coupon(coupon)
        self.assertEqual(cart.serialize(), {'cart': [{'coupon': '12341234', 'quantity': 1, 'uid': 'Some'},
                                                     {'coupon': None, 'quantity': 12, 'uid': 'Another'},
                                                     {'coupon': None, 'quantity': 2, 'uid': 'YetAnother'}]})

    def test_shopping_cart_unserialize(self):
        coupon = Coupon(title="Awesome offer!!!",
                        code='12341234',
                        subscription=SomeSubscription.uid,
                        discount_percent=90.0)
        coupon.save()

        serialized_cart = {'cart': [{'coupon': '12341234', 'quantity': 1, 'uid': 'Some'},
                                    {'coupon': None, 'quantity': 12, 'uid': 'Another'},
                                    {'coupon': None, 'quantity': 2, 'uid': 'YetAnother'}]}
        cart = ShoppingCart.unserialize(serialized_cart)

        self.assertEqual(len(cart), 3)

        self.assertEqual(cart[0].coupon, coupon)
        self.assertEqual(cart[0].quantity, 1)
        self.assertEqual(cart[0].item.uid, 'Some')

        self.assertEqual(cart[1].coupon, None)
        self.assertEqual(cart[1].quantity, 12)
        self.assertEqual(cart[1].item.uid, 'Another')

        self.assertEqual(cart[2].coupon, None)
        self.assertEqual(cart[2].quantity, 2)
        self.assertEqual(cart[2].item.uid, 'YetAnother')
