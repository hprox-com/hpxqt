import os
from datetime import datetime

from pony import orm as pony_orm

from hpxqt import settings

db = pony_orm.Database()

class User(db.Entity):
    email = pony_orm.Required(str)
    password = pony_orm.Required(str)


class Update(db.Entity):
    version = pony_orm.Required(str)
    date = pony_orm.Required(datetime, default=datetime.now)
    is_installed = pony_orm.Required(bool, default=False)


class DatabaseManager(object):

    def initialize(self):
        create = not os.path.exists(settings.DB_FILE)

        db.bind(provider='sqlite',
                filename=settings.DB_FILE,
                create_db=create)

        db.generate_mapping(create_tables=True)


    @pony_orm.db_session
    def add_user(self, email, password):
        User(email=email, password=password)

    @pony_orm.db_session
    def add_update(self, version, installed=False):
        Update(version=version,
               is_installed=installed)

    @pony_orm.db_session
    def set_last_update_installed(self):
        update = pony_orm.select(u for u in Update if not u.is_installed)\
                        .order_by(self.modelUpdate.date).first()
        update.is_installed = True

    @pony_orm.db_session
    def delete_user(self, email):
        pony_orm.delete(u for u in User if u.email == email)

    @pony_orm.db_session
    def delete_update(self, version):
        pony_orm.delete(u for u in Update if u.version == version)

    @pony_orm.db_session
    def last_update(self):
        return pony_orm.select(u for u in Update).order_by(Update.date).first()

    @pony_orm.db_session
    def last_user(self):
        return pony_orm.select(u for u in User).order_by(User.id).first()

    @pony_orm.db_session
    def get_user(self, email):
        return pony_orm.select(u for u in User if u.email == email).first()

    @pony_orm.db_session
    def get_update(self, version):
        return pony_orm.select(u for u in Update if u.version == version).first()
