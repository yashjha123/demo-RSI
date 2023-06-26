import pymysql
import pandas as pd
import sshtunnel


import operator


sshtunnel.SSH_TIMEOUT = 5.0
sshtunnel.TUNNEL_TIMEOUT = 5.0

FORCE_RECONNECT = True 

def azip(a,b):
    ret = []
    for c in zip(a,b):
        ret.append([c[0]]+c[1])
    print(ret)
    return ret
def ltos(s):
 
    # initialize an empty string
    str1 = ","
 
    # return string
    return (str1.join(s))
     

def ltons(s):
 
    # initialize an empty string
    str1 = ","
 
    # return string
    ret = (str1.join(s))
    print(ret)
    return ret

def tof(s):
    return ",".join(["%s"]*len(s))
class NiceDB:
    def __init__(self):
        self.server =  sshtunnel.SSHTunnelForwarder(
            ('ssh.pythonanywhere.com'),
            ssh_username='demoRSI', ssh_password='DEMORSI1234567',
            remote_bind_address=('demoRSI.mysql.pythonanywhere-services.com', 3306)
        )

    def start(self):
        self.server.start()

        self.connection = pymysql.connect(
            user='demoRSI',
            passwd='geotranslab',
            host='127.0.0.1', port=self.server.local_bind_port,
            db='demoRSI$archive',
        )
        self.cursor = self.connection.cursor(pymysql.cursors.DictCursor)

    def test(self):
        conn = self.connection
        query = '''SELECT VERSION();'''
        data = pd.read_sql_query(query, conn)
        # Expected output
        #   VERSION()
        # 0    8.0.32
        print(data)

    def close(self):
        self.connection.close()
        self.server.stop()

    def commit(self):
        self.connection.commit()

    def reconnect(self):
        self.connection.ping()
class NiceTable:
    def __init__(self,db:NiceDB,table,key="id",value=None,high_load=False):
        self.db = db
        self.table = table
        self.key = key
        self.high_load = high_load
        self.value = value
        if isinstance(value,list): self.iter = operator.itemgetter(*value)
        else: self.iter = operator.itemgetter(value)
    def flush(self):
        self.db.commit()
    def __getitem__(self,index):
        self.db.reconnect()
        cursor = self.db.cursor
        if self.value:
            if type(self.value) == list:
                cursor.execute(f"SELECT {ltos(self.value+[self.key])} FROM {self.table} WHERE {self.key} = '{index}'")
                for row in cursor:
                    ret = {}
                    for value in self.value:
                        print(value)
                        ret[value] = row[value]
                    return ret
            else:
                cursor.execute(f"SELECT * FROM {self.table} WHERE {self.key} = '{index}'")
                for row in cursor:
                    return row[self.value]    
        else:
            cursor.execute(f"SELECT * FROM {self.table} WHERE {self.key} = '{index}'")
            for row in cursor:
                return row
    def __contains__(self,index):
        self.db.reconnect()
        cursor = self.db.cursor
        cursor.execute(f"SELECT * FROM {self.table} WHERE {self.key} = '{index}'")
        for row in cursor:
            return True
        return False
    def __setitem__(self,index,value):
        self.db.reconnect()
        cursor = self.db.cursor
        if self.high_load:
            cursor.execute(f"INSERT INTO {self.table} ({self.key}, {','.join(self.value)}) VALUES ('{index}'{',%s'*len(value)});",value)
            return
        if type(self.value) == list:
            if self.key in self.value:
                values = self.value.copy()
                values.remove(self.key)
            else:
                values = self.value
            cursor.execute(f"INSERT INTO {self.table} ({self.key}, {','.join(values)}) VALUES ('{index}', '{','.join(value)}');")
        else:
            cursor.execute(f"INSERT INTO {self.table} ({self.key}, {self.value}) VALUES ('{index}', '{value}');")
        

class BulkTable(NiceTable):
    def __getitem__(self, index):
        self.db.reconnect()
        if type(index) != list:
            index = [index]
        # "select * from info WHERE `id` IN ($ids)"
        if(len(index)==0): return []
        cursor = self.db.cursor
        cursor.execute(f"SELECT {ltos([self.key]+self.value)} FROM {self.table} WHERE {self.key} IN ({tof(index)})",index)
        ret = {}
        for row in cursor:
            ret[row[self.key]] = self.iter(row)
        return ret
    def __setitem__(self, index, value):
        self.db.reconnect()
        # for val in :
        cursor = self.db.cursor
        print(list(azip(index,value)))
        cursor.executemany(f"INSERT INTO {self.table} ({self.key}, {','.join(self.value)}) VALUES ({ltons(['%s']*(len(self.value)+1))});",azip(index,value))

# CREATE TABLE RWIS_PRED (IMAGE_URL VARCHAR(2083) NOT NULL,
#           Snow_Estimate_Ratio float,
#           SRC_MASK LONGBLOB INVISIBLE);
#
# CREATE TABLE RWIS_PRED (IMAGE_URL VARCHAR(2083) NOT NULL,
#           Bare float,
#           PartlySnowCoverage float,
#           Undefined float,
#           FullSnowCoverage float);
# mysql> ALTER TABLE RWIS_PRED ALTER COLUMN SRC_MASK SET INVISIBLE;

# mysql> 
import base64
from PIL import Image
import io
if __name__ == "__main__":
    db = NiceDB()
    db.start()
    sample_image = "https://mesonet.agron.iastate.edu/archive/data/2023/06/07/camera/IDOT-047-00/IDOT-047-00_202306071929.jpg"
    disksave = NiceTable(db,"RWIS_PRED",key="IMAGE_URL",value=["Snow_Estimate_Ratio","SRC_MASK"],high_load=True)
    # disksave = NiceTable(db,"AVL_PRED",key="IMAGE_URL",value=["Bare","PartlySnowCoverage","Undefined","FullSnowCoverage"],high_load=True)
    disksave[sample_image] = [0,0,1,0]
    # disksave.flush()
    bulk_save = BulkTable(db,"AVL_PRED",key="IMAGE_URL",value=["Bare","PartlySnowCoverage","Undefined","FullSnowCoverage"],high_load=True)
    # print(bulk_save[sample_image])
    img2 = "https://mesonet.agron.iastate.edu/archive/data/2023/05/23/camera/IDOT-014-00/IDOT-014-00_202305232357.jpg"
    print(bulk_save[["AA","BB"]])

    # img1 = "AA"
    # img2 = "BB"
    # bulk_save[[img1,img2]]=[[.5,.5,.5,.5],[1,1,1,1]]
    # bulk_save.flush()
    # print()

    # file = open('image.png','rb').read()
 
    # We must encode the file to get base64 string
    # file = base64.b64encode(file)
    # file = bytes("ABC","utf-8")
    # disksave[sample_image] = ["0.1",file]
    # disksave.flush()
    # print((disksave[sample_image]['SRC_MASK']).decode())
    # print(disksave[sample_image])
    # print(disksave[sample_image])
    # print(disksave[sample_image])
    # disksave["a"]=.10
    # print("a" in disksave)
    # print("GARBAGEVALUE" in disksave)
    # print(disksave["a"])


    # disksave_tb = NiceTable(db,"RWIS_PRED",key="IMAGE_URL",value=["Snow_Estimate_Ratio","IMAGE_URL"])
    # print(disksave_tb["aa"])
    # disksave_tb["aa"]=["0.123"]s
