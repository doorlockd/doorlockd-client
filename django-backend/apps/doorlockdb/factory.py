

import factory 
from .import models 
import random
# from apps.doorlockdb.models import *


def seed_persons(x_pers=9, x_keys=2):
    for p in range(x_pers):
        p = RandomPerson()
        p.save()
        print(p)
        for k in range(x_keys):
            k =  RandomKey(owner=p)
            print(k)
        
        # give random group permisions
        for x in range(random.choice((0,1,2,3,4,5,6,1,1,2,3,2,1))):
            g = random.choices( models.PersonGroup.objects.all())[0]
            p.personsgroup.add(g)
            print(g)
    print("")
        
        

    


def seed_model(amount, model):
    result = []
    for i in range(0, amount):
        o = model()
        print("NEW: ", model, o)
        o.save()
        result.append(o)
    return(result)
    

def seed_db(add_locks=[]):
    # create 5 Locks:
    locks = []
    locks.extend(add_locks)

    for l_i in range(0, 4):
        l = RandomLock()
        l.save()
        print("NEW:", l)
        locks.append(l)

    # create 10 persons:
    for p_i in range(0, 9):
        p = RandomPerson()
        p.save()
        print("NEW:", p)
        
        # add 4 Keys:
        for k_i in range(0,3):
            k =  RandomKey(owner=p)
            # k.owner = p
            k.save()
            print("NEW:", k)
    
        # permisions per lock:
        for l in locks:
            # random give acces:
            if random.choice((True, False)):
                print("Access:", l, p)
                p.access.add(l)


def random_hwid(): 
    """Generate random hwid, 4 or 7 bytes, never starting with ^08:... """
    hwid =  ':'.join('%02x'%random.randint(0,255) for x in range(random.choice([4,7])))
    # avoid random id's:
    if (hwid[0:2] == '08'):
        # generate new one:
        hwid = random_hwid()

    return hwid


class RandomPerson(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Person

    name = factory.Faker('name')
    email = factory.Faker('email')
    info = factory.Faker('text')
    # is_enabled = factory.Faker('pybool')
    is_enabled = random.choice((True, False,True, True, True, True, True))


class RandomLock(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Lock

    name = factory.Faker('word')
    description = factory.Faker('text')
    # is_enabled = factory.Faker('pybool')
    is_enabled = random.choice((True, False,True, True))

class RandomKey(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Key

    # TODO: fix , prevent 08:....
    # hwid = factory.Faker('mac_address')
    hwid = factory.LazyFunction(random_hwid)

    description = factory.Faker('text')
    # is_enabled = factory.Faker('pybool')
    is_enabled = random.choice((True, False,True, True, True, True))

