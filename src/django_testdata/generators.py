# -*- coding: utf-8 -*-
from decimal import Decimal
import datetime
import random
import string


class Generator(object):
    coerce_type = staticmethod(lambda x: x)

    def __init__(self, none_chance=0, coerce=None):
        self.none_chance = none_chance
        if coerce:
            self.coerce_type = coerce

    def coerce(self, value):
        return self.coerce_type(value)

    def generate(self):
        raise NotImplementedError

    def get_value(self):
        if random.random() < self.none_chance:
            return None
        value = self.generate()
        return self.coerce(value)


class StaticGenerator(Generator):
    def __init__(self, value, *args, **kwargs):
        self.value = value
        super(StaticGenerator, self).__init__(*args, **kwargs)

    def generate(self):
        return self.value


class NoneGenerator(Generator):
    def generate(self):
        return None


class BooleanGenerator(Generator):
    coerce_type = bool

    def generate(self):
        return random.choice((True, False))


class StringGenerator(Generator):
    coerce_type = unicode

    def __init__(self, chars=None, multiline=False, min_length=0, max_length=1000, *args, **kwargs):
        assert min_length >= 0
        assert max_length >= 0
        self.chars = chars
        self.min_length = min_length
        self.max_length = max_length
        if self.chars is None:
            self.chars = string.letters
            if multiline:
                self.chars += string.whitespace
            else:
                self.chars += ' '
        super(StringGenerator, self).__init__(*args, **kwargs)

    def generate(self):
        length = random.randint(self.min_length, self.max_length)
        value = u''
        for x in xrange(length):
            value += random.choice(self.chars)
        return value


class LoremGenerator(StringGenerator):
    pass


class IntegerGenerator(Generator):
    coerce_type = int

    def __init__(self, min_value=-2**32, max_value=2**32-1, *args, **kwargs):
        self.min_value = min_value
        self.max_value = max_value
        super(IntegerGenerator, self).__init__(*args, **kwargs)

    def generate(self):
        value = random.randint(self.min_value, self.max_value)
        return value


class PositiveIntegerGenerator(IntegerGenerator):
    coerce_type = abs


class ChoicesGenerator(Generator):
    def __init__(self, choices=(), values=(), *args, **kwargs):
        assert len(choices) or len(values)
        self.choices = list(choices)
        if not values:
            self.values = [k for k, v in self.choices]
        else:
            self.values = list(values)
        super(ChoicesGenerator, self).__init__(*args, **kwargs)

    def generate(self):
        return random.choice(self.values)


class DateTimeGenerator(Generator):
    def __init__(self, min_date=None, max_date=None, *args, **kwargs):
        self.min_date = min_date or datetime.datetime.min
        self.max_date = max_date or datetime.datetime.max
        assert self.min_date < self.max_date
        super(DateTimeGenerator, self).__init__(*args, **kwargs)

    def generate(self):
        diff = self.max_date - self.min_date
        seconds = random.randint(0, diff.days * 3600 * 24 + diff.seconds)
        return self.min_date + datetime.timedelta(seconds=seconds)


class DateGenerator(Generator):
    def __init__(self, min_date=None, max_date=None, *args, **kwargs):
        self.min_date = min_date or datetime.date.min
        self.max_date = max_date or datetime.date.max
        assert self.min_date < self.max_date
        super(DateGenerator, self).__init__(*args, **kwargs)

    def generate(self):
        diff = self.max_date - self.min_date
        days = random.randint(0, diff.days)
        date = self.min_date + datetime.timedelta(days=days)
        return date
        return datetime.date(date.year, date.month, date.day)

class DecimalGenerator(Generator):
    coerce_type = Decimal

    max_digits = 24
    decimal_places = 10

    def __init__(self, max_digits=None, decimal_places=None, *args, **kwargs):
        if max_digits is not None:
            self.max_digits = max_digits
        if decimal_places is not None:
            self.decimal_places = decimal_places
        super(DecimalGenerator, self).__init__(*args, **kwargs)

    def generate(self):
        maxint = 10 ** self.max_digits - 1
        value = (
            Decimal(random.randint(-maxint, maxint)) /
            10 ** self.decimal_places)
        return value

class EmailGenerator(StringGenerator):
    def __init__(self, chars=None, max_length=100, tlds=None, *args, **kwargs):
        assert max_length >= 6
        if chars is None:
            chars = string.ascii_lowercase
        self.tlds = tlds
        super(EmailGenerator, self).__init__(chars, max_length=max_length, *args, **kwargs)

    def generate(self):
        maxl = self.max_length - 2
        if self.tlds:
            tld = random.choice(self.tlds)
        elif maxl > 4:
            tld = StringGenerator(self.chars, min_length=3, max_length=3).generate()
        maxl -= len(tld)
        assert maxl >= 2

        name = StringGenerator(self.chars, min_length=1, max_length=maxl-1).generate()
        maxl -= len(name)
        domain = StringGenerator(self.chars, min_length=1, max_length=maxl).generate()
        return '%s@%s.%s' % (name, domain, tld)


class IPAddressGenerator(Generator):
    coerce_type = unicode

    def generate(self):
        return '.'.join([unicode(part) for part in [
            IntegerGenerator(min_value=1, max_value=254).generate(),
            IntegerGenerator(min_value=0, max_value=254).generate(),
            IntegerGenerator(min_value=0, max_value=254).generate(),
            IntegerGenerator(min_value=1, max_value=254).generate(),
        ]])