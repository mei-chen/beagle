import inspect

from django.utils.decorators import method_decorator

from .subscriptions import Subscription
from .exceptions import ShoppingCartInvalidQuantityException, \
    ShoppingCartInvalidItemException, CouponNotApplicableException, ShoppingCartCurrencyMismatchException


def price_f(f):
    """
    Round the decimals of the return value of a function
    """
    def decorated_f(*args, **kwargs):
        price = f(*args, **kwargs)
        if isinstance(price, (int, float)):
            return round(price, 2)
        return 0.0
    return decorated_f


class ShoppingCartItem:
    def __init__(self, item, quantity):
        """
        :param item: The item bought - should have a relevant __str__ or __unicode__ implementation
        :param quantity: The quantity of the item bought
        """
        if not isinstance(quantity, int) or quantity < 0:
            raise ShoppingCartInvalidQuantityException("Quantity should be integer and greater than 0")

        if not inspect.isclass(item) or not issubclass(item, Subscription):
            raise ShoppingCartInvalidItemException("Please provide a subscription as a Shopping cart Item")

        self.item = item
        self.quantity = quantity
        self.coupon = None

    @staticmethod
    def unserialize(d):
        from marketing.models import Coupon
        item = ShoppingCartItem(Subscription.get_by_uid(d['uid']), d['quantity'])
        if 'coupon' in d and d['coupon']:
            item.apply_coupon(Coupon.get_by_code(d['coupon']))

        return item

    @property
    @method_decorator(price_f)
    def item_price(self):
        if self.coupon is None:
            return self.item.price

        return self.coupon.purchase_price

    @property
    @method_decorator(price_f)
    def total_price(self):
        """
        Price paid for the bundle Quantity * Price_Per_Item
        :return: total_price
        """
        return self.item_price * self.quantity

    def coupon_applies(self, coupon):
        """
        Check if a coupon Django Model applies to this cart item
        """
        if not coupon.is_available:
            return False

        if coupon.get_subscription() != self.item:
            return False

        return True

    def apply_coupon(self, coupon):
        """
        Apply the coupon (save the coupon)
        """
        if not self.coupon_applies(coupon):
            raise CouponNotApplicableException("The coupon does not apply to this subscription")

        self.coupon = coupon

    def serialize(self):
        return {
            'uid': self.item.uid,
            'quantity': self.quantity,
            'coupon': self.coupon.code if self.coupon else None
        }

    def __repr__(self):
        return repr((self.item, self.quantity))

    def __str__(self):
        return "Item={}, Quantity={}, Total={}".format(self.item, self.quantity, self.total_price)


class ShoppingCart:
    """
    Simple class for managing a shopping cart
    """

    SESSION_KEY = 'ShoppingCart'

    @staticmethod
    def unserialize(d):
        item_list = d['cart']
        cart = ShoppingCart()
        for serialized_item in item_list:
            cart.add_item(ShoppingCartItem.unserialize(serialized_item))

        return cart

    @staticmethod
    def get_from_session(request):
        serialized_cart = request.session.get(ShoppingCart.SESSION_KEY)
        if serialized_cart is None:
            return None

        return ShoppingCart.unserialize(serialized_cart)

    @staticmethod
    def delete_from_session(request):
        try:
            del request.session[ShoppingCart.SESSION_KEY]
        except KeyError:
            pass

    def __init__(self):
        self._items = []

    def _check_currency(self, item):
        if not self._items:
            return True

        if self._items[-1].item.currency != item.item.currency:
            raise ShoppingCartCurrencyMismatchException("Currencies do not match")

    def add(self, item, quantity):
        """
        Add to cart by numbers
        """
        self.add_item(ShoppingCartItem(item, quantity))

    def add_item(self, cart_item):
        """
        Add to cart a ShoppingCartItem
        """
        self._check_currency(cart_item)
        for item in self._items:
            if item.item == cart_item.item:
                item.quantity += cart_item.quantity
                return
        self._items.append(cart_item)

    def apply_coupon(self, coupon):
        """
        Apply the coupon
        """

        for item in self._items:
            if item.coupon_applies(coupon):
                item.apply_coupon(coupon)
                return True
        return False

    def serialize(self):
        return {'cart': [item.serialize() for item in self]}

    def save_to_session(self, request):
        request.session[ShoppingCart.SESSION_KEY] = self.serialize()

    @property
    def distinct_count(self):
        """
        The number of distinct items in the shopping cart
        """
        return len(self._items)

    @property
    def total_count(self):
        """
        The total number of items in the shopping cart
        """
        return sum([item.quantity for item in self._items])

    @property
    @method_decorator(price_f)
    def total_price(self):
        """
        The total price of the shopping cart
        :return:
        """
        return sum([item.total_price for item in self._items])

    @property
    def currency(self):
        """
        The currency of the shopping cart
        :return:
        """
        if self._items:
            return self._items[0].item.currency
        return None

    @property
    def is_free(self):
        """
        Is the shopping cart free?
        :return: True/False
        """
        return self.total_price == 0.0

    def __getitem__(self, index):
        if index in ['total_price', 'distinct_count', 'total_count', 'currency']:
            return getattr(self, index, None)

        if isinstance(index, int):
            return self._items[index]

        for item in self._items:
            if item.item == index or item.item.uid == index:
                return item

        return None

    def __iter__(self):
        return iter(self._items)

    def __len__(self):
        return len(self._items)

    def __str__(self):
        return str(self.__class__) + "<" + str(self._items) + ">"
