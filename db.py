import os
from datetime import datetime

from pony import orm as pony_orm

from hpxqt import utils as hpxqt_utils


DB = pony_orm.Database()


class User(DB.Entity):
    email = pony_orm.Required(str)
    password = pony_orm.Required(str)
    password = pony_orm.Required(str)


class Update(DB.Entity):
    version = pony_orm.Required(str)
    date = pony_orm.Required(datetime, default=datetime.now)
    is_installed = pony_orm.Required(bool, default=False)


class DatabaseManager(object):

    def initialize(self):
        DB.bind(provider='sqlite',
                filename=hpxqt_utils.get_db_file_path(),
                create_db=not os.path.exists(hpxqt_utils.get_db_file_path()))

        DB.generate_mapping(create_tables=True)


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
    def delete_user(self):
        pony_orm.delete(u for u in User)

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
