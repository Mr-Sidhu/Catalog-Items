"""Popualtes the database with dummy data to have\
something to display during the development of the application."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from catalog_Db import Catalog, Base, CatalogItems, User

engine = create_engine('sqlite:///ItemCatalog.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

# Create dummmy user
User1 = User(name="Raja Sidhu", email="RajaSidhu@udacity.com",
             picture='https://pbs.twimg.com/profile_images/2671170543/18debd694829ed78203a5a36dd364160_400x400.png')  # NOQA

session.add(User1)

session.commit()

# first catalog
catalog1 = Catalog(user_id=1, name="Soccer")

session.add(catalog1)
session.commit()

catalog2 = Catalog(user_id=1, name="Basketball")
session.add(catalog2)
session.commit()

catalog3 = Catalog(user_id=1, name="Baseball")
session.add(catalog3)
session.commit()

catalog4 = Catalog(user_id=1, name="Frisbee")
session.add(catalog4)
session.commit()

catalog5 = Catalog(user_id=1, name="Snowboarding")
session.add(catalog5)
session.commit()

catalog6 = Catalog(user_id=1, name="Rock Climbing")
session.add(catalog6)
session.commit()

catalog7 = Catalog(user_id=1, name="Foosball")
session.add(catalog7)
session.commit()

catalog8 = Catalog(user_id=1, name="Skating")
session.add(catalog8)
session.commit()

catalog9 = Catalog(user_id=1, name="Hockey")
session.add(catalog9)
session.commit()

# first catalog item. dummy data for development purposes.
catalogItem1 = CatalogItems(user_id=1, name="Two Shinguards",
                            description="To protect your shins",
                            userEmail="RajaSidhu@udacity.com",
                            catalog=catalog1)

session.add(catalogItem1)
session.commit()

catalogItem2 = CatalogItems(user_id=1, name="Goggles",
                            description="Protect your eyes while Snowboarding",
                            userEmail="RajaSidhu@udacity.com",
                            catalog=catalog5)

session.add(catalogItem2)
session.commit()

print "Items have been added to catalog."
