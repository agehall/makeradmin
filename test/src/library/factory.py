from factory import Faker, Factory, LazyAttribute, Sequence


class MemberFactory(Factory):
    class Meta:
        model = dict
    
    email = Faker('email')
    firstname = Faker('first_name')
    lastname = Faker('last_name')
    password = LazyAttribute(lambda o: "1q2w3e")
    address_street = Faker('street_name')
    address_extra = LazyAttribute(lambda o: "N/A")
    address_zipcode = Sequence(lambda n: 10200 + n)
    address_city = Faker('city')
    address_country = Faker('country_code', representation="alpha-2")
    phone = Sequence(lambda n: f'070-{n:07d}')
    civicregno = Sequence(lambda n: f"19901011{9944 + n:04d}")