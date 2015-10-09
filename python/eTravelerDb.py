import ConfigParser
import MySQLdb as db2Imp

class Parfile(dict):
    def __init__(self, infile, section):
        super(Parfile, self).__init__()
        parser = ConfigParser.ConfigParser()
        parser.read(infile)
        for key, value in parser.items(section):
            self[key] = self._cast(value)
    def _cast(self, value):
        try:
            if value.find('.') == -1 and value.find('e') == -1:
                return int(value)
            else:
                return float(value)
        except ValueError:
            # Cannot cast as either int or float so just return the
            # value as-is (presumably a string).
            return value

def nullFunc(*args):
    return None

class DbInterface(object):
    def __init__(self, credentials_file, section):
        self.pars = Parfile(credentials_file, section)
        self._connection = db2Imp.connect(**self.pars)
    def apply(self, sql, args=None, cursorFunc=nullFunc):
        sql = sql.replace('?', '%s')
        cursor = self._connection.cursor()
        results = None
        try:
            if args is None:
                cursor.execute(sql)
            else:
                cursor.execute(sql, args)
            results = cursorFunc(cursor)
        except db2Imp.DatabaseError, message:
            cursor.close()
            raise db2Imp.DatabaseError(message)
        cursor.close()
        if cursorFunc is nullFunc:
            self._connection.commit()
        return results

class eTravelerDb(DbInterface):
    def __init__(self, credentials_file, section='eTraveler_dev'):
        super(eTravelerDb, self).__init__(credentials_file, section)
    def processInfo(self, processName):
        sql = "select * from Process where name = '%s'" % processName
        return self.apply(sql, cursorFunc=lambda cursor : [x for x in cursor])

if __name__ == '__main__':
    db_parfile = 'eTraveler_db_info.par'

    db = eTravelerDb(db_parfile)

    print db.pars

    def cursorFunc(cursor):
        return [entry for entry in cursor]

    print db.apply("select * from Process where name='flat_acq'",
                   cursorFunc=cursorFunc)

    print db.processInfo('xtalk_acq')
