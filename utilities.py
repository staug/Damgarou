import pygame as pg
from default import *
import random as rd

# Set of utilities


def roll(dice, repeat=1):
    """
    Roll one or multiple dice(s)
    :param dice: the type of dice - 6 for d6, 8 for d8...
    :param repeat: the number of dices of same tye to roll
    :return: the value
    """
    res = 0
    for i in range(repeat):
        res += rd.randint(1, dice)
    return res


class Ticker(object):
    """Simple timer for roguelike games."""

    def __init__(self):
        self.ticks = 0  # current ticks--sys.maxint is 2147483647
        self.schedule = {}  # this is the dict of things to do {ticks: [obj1, obj2, ...], ticks+1: [...], ...}
        self.ticks_to_advance = 0

    def schedule_turn(self, interval, obj):
        self.schedule.setdefault(self.ticks + interval, []).append(obj)

    def _advance_ticks(self, interval):
        for i in range(interval):
            things_to_do = self.schedule.pop(self.ticks, [])
            for obj in things_to_do:
                if obj is not None:
                    obj.take_turn()
            self.ticks += 1

    def advance_ticks(self):
        if self.ticks_to_advance > 0:
            self._advance_ticks(self.ticks_to_advance)
            self.ticks_to_advance = 0

    def unregister(self, obj):
        if obj is not None:
            for key in self.schedule.keys():
                while obj in self.schedule[key]:
                    self.schedule[key].remove(obj)


class Publisher(object):
    """
    Dispatch messages
    Messages have two categories (defined in constants):
    * Main: like log, fight, exploration, inventory
    * Sub: precises the main, optional.
    Messgae content is a dictionary
    """
    CATEGORY_ALL = "*"

    def __init__(self):
        self._specialized_list = {}  # Subscribe to main and a list of sub_category
        self.in_publish = False
        self.delayed_unregister = []

    def register(self,
                 object_to_register,
                 main_category=CATEGORY_ALL,
                 sub_category=CATEGORY_ALL,
                 function_to_call=None):
        """
        Register an object so that we can pass him an object
        :param object_to_register: the object that will be notified.
        Note that the same object may be registered multiple time, with different functions to be called or
        different category of interest, so that we are effectively saving the method only
        :param main_category: one or multiple (in list) categories to register.
        :param sub_category: one or multiple (in list) specialized sub categories to register
        :param function_to_call: the method to be called.
        :return:
        """
        if function_to_call is None:
            assert hasattr(object_to_register, "notify"), \
                "Object {} has no notify method and has not precised the " \
                "function to be called".format(object_to_register)
            function_to_call = getattr(object_to_register, "notify")
        if type(sub_category) is not (list or tuple):
            sub_category = [sub_category]
        if type(main_category) is not (list or tuple):
            main_category = [main_category]
        for category in main_category:
            for sub in sub_category:
                key = "{}#{}".format(category, sub)
                if key not in self._specialized_list.keys():
                    self._specialized_list[key] = [function_to_call]
                elif function_to_call not in self._specialized_list[key]:
                    self._specialized_list[key].append(function_to_call)

    def unregister_all(self, object_to_unregister):
        # We need to parse all the lists..
        # and the same object may have been registered with different functions
        if self.in_publish:
            self.delayed_unregister.append(object_to_unregister)
        else:
            for key in self._specialized_list.keys():
                list_to_remove = []
                list_to_parse = self._specialized_list[key]
                for function_called in list_to_parse:
                    if function_called.__self__ == object_to_unregister:
                        list_to_remove.append(function_called)
                for function_called in list_to_remove:
                    self._specialized_list[key].remove(function_called)

    def handle_delayed_unregister_all(self):
        for object_to_unregister in self.delayed_unregister:
            self.unregister_all(object_to_unregister)

    def publish(self, source, message, main_category=CATEGORY_ALL, sub_category=CATEGORY_ALL):
        self.in_publish = True
        assert type(message) is dict, "Message {} is not a dict".format(message)
        message["SOURCE"] = source
        broadcasted_list = []
        message["MAIN_CATEGORY"] = main_category
        message["SUB_CATEGORY"] = sub_category
        if type(sub_category) is not (list or tuple):
            sub_category = [sub_category]
        if type(main_category) is not (list or tuple):
            main_category = [main_category]

        # By default, we always broadcast to "ALL"
        if Publisher.CATEGORY_ALL not in main_category:
            main_category.append(Publisher.CATEGORY_ALL)
        if Publisher.CATEGORY_ALL not in sub_category:
            sub_category.append(Publisher.CATEGORY_ALL)

        for category in main_category:
            for sub in sub_category:
                message["BROADCAST_MAIN_CATEGORY"] = category
                message["BROADCAST_SUB_CATEGORY"] = category
                key = "{}#{}".format(category, sub)
                if key in self._specialized_list:
                    for function_called in self._specialized_list[key]:
                        if function_called not in broadcasted_list:  # Need to be sure not to send two times the message
                            function_called(message)
                            broadcasted_list.append(function_called)
        self.in_publish = False
        self.handle_delayed_unregister_all()


class Logger:

    ERROR = 5
    WARN = 4
    INFORM = 3
    DEBUG = 2
    TRACE = 1
    LABELS = ("", "[TRACE] ", "[DEBUG] ", "[INFORM] ","[WARN] ", "[ERROR] ")

    def __init__(self):
        self._log_level = Logger.TRACE

    def log(self, message, level=INFORM):
        if level >= self._log_level:
            self.out(Logger.LABELS[level] + message)

    def out(self, message):
        print(message)

    def handle_published_message(self, message):
        self.out("[MESSAGE] " + message)

    def trace(self, message):
        self.log(message, level=Logger.TRACE)

    def debug(self, message):
        self.log(message, level=Logger.DEBUG)

    def inform(self, message):
        self.log(message, level=Logger.INFORM)

    def warn(self, message):
        self.log(message, level=Logger.WARN)

    def error(self, message):
        self.log(message, level=Logger.ERROR)


class EmptyLogger(Logger):

    def out(self, message):
        pass

    def handle_published_message(self, message):
        pass

# A STAR Algo
# Version 1.1
#
# Changes in 1.1:
# In order to optimize the list handling I implemented the location id (lid) attribute.
# This will make the all list serahces to become extremely more optimized.

class Path:
    def __init__(self, nodes, totalCost):
        self.nodes = nodes;
        self.totalCost = totalCost;

    def getNodes(self):
        return self.nodes

    def getTotalMoveCost(self):
        return self.totalCost


class Node:
    def __init__(self, location, mCost, lid, parent=None):
        self.location = location  # where is this node located
        self.mCost = mCost  # total move cost to reach this node
        self.parent = parent  # parent node
        self.score = 0  # calculated score for this node
        self.lid = lid  # set the location id - unique for each location in the map

    def __eq__(self, n):
        if n.lid == self.lid:
            return 1
        else:
            return 0


class AStar:
    def __init__(self, maphandler):
        self.mh = maphandler

    def _getBestOpenNode(self):
        bestNode = None
        for n in self.on:
            if not bestNode:
                bestNode = n
            else:
                if n.score <= bestNode.score:
                    bestNode = n
        return bestNode

    def _tracePath(self, n):
        nodes = [];
        totalCost = n.mCost;
        p = n.parent;
        nodes.insert(0, n);

        while 1:
            if p.parent is None:
                break

            nodes.insert(0, p)
            p = p.parent

        return Path(nodes, totalCost)

    def _handleNode(self, node, end):
        i = self.o.index(node.lid)
        self.on.pop(i)
        self.o.pop(i)
        self.c.append(node.lid)

        nodes = self.mh.getAdjacentNodes(node, end)

        for n in nodes:
            if n.location == end:
                # reached the destination
                return n
            elif n.lid in self.c:
                # already in close, skip this
                continue
            elif n.lid in self.o:
                # already in open, check if better score
                i = self.o.index(n.lid)
                on = self.on[i];
                if n.mCost < on.mCost:
                    self.on.pop(i);
                    self.o.pop(i);
                    self.on.append(n);
                    self.o.append(n.lid);
            else:
                # new node, append to open list
                self.on.append(n);
                self.o.append(n.lid);

        return None

    def findPath(self, fromlocation, tolocation):
        self.o = []
        self.on = []
        self.c = []

        end = tolocation
        fnode = self.mh.getNode(fromlocation)
        self.on.append(fnode)
        self.o.append(fnode.lid)
        nextNode = fnode

        while nextNode is not None:
            finish = self._handleNode(nextNode, end)
            if finish:
                return self._tracePath(finish)
            nextNode = self._getBestOpenNode()

        return None


class SQ_Location:
    """A simple Square Map Location implementation"""

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, l):
        """MUST BE IMPLEMENTED"""
        if l.x == self.x and l.y == self.y:
            return 1
        else:
            return 0


class SQ_MapHandler:
    """A simple Square Map implementation"""

    def __init__(self, mapdata, width, height):
        self.m = mapdata
        self.w = width
        self.h = height

    def getNode(self, location):
        """MUST BE IMPLEMENTED"""
        x = location.x
        y = location.y
        if x < 0 or x >= self.w or y < 0 or y >= self.h:
            return None
        tile = self.m[x][y]
        if tile.tile_type != '2':  # Not a ground
            return None
        #d = self.m[(y*self.w)+x]
        #if d == -1:
        #    return None
        d = 1
        return Node(location, d, ((y * self.w) + x));

    def getAdjacentNodes(self, curnode, dest):
        """MUST BE IMPLEMENTED"""
        result = []

        cl = curnode.location
        dl = dest

        n = self._handleNode(cl.x + 1, cl.y, curnode, dl.x, dl.y)
        if n: result.append(n)
        n = self._handleNode(cl.x - 1, cl.y, curnode, dl.x, dl.y)
        if n: result.append(n)
        n = self._handleNode(cl.x, cl.y + 1, curnode, dl.x, dl.y)
        if n: result.append(n)
        n = self._handleNode(cl.x, cl.y - 1, curnode, dl.x, dl.y)
        if n: result.append(n)

        return result

    def _handleNode(self, x, y, fromnode, destx, desty):
        n = self.getNode(SQ_Location(x, y))
        if n is not None:
            dx = max(x, destx) - min(x, destx)
            dy = max(y, desty) - min(y, desty)
            emCost = dx + dy
            n.mCost += fromnode.mCost
            n.score = n.mCost + emCost
            n.parent = fromnode
            return n

        return None


NAMES = ["Abaet","Acamen","Adeen","Aghon","Ahburn","Airen","Aldaren","Alkirk","Amitel","Anumil","Asen","Atgur","Auden","Aysen","Abarden","Achard","Aerden","Agnar","Ahdun","Airis","Alderman","Allso","Anfar","Asden","Aslan","Atlin","Ault","Aboloft","Ackmard","Afflon","Ahalfar","Aidan","Albright","Aldren","Amerdan","Anumi","Asdern","Atar","Auchfor","Ayrie",
"Bacohl","Balati","Basden","Bedic","Beson","Bewul","Biston","Boaldelr","Breanon","Bredock","Bristan","Busma","Badeek","Baradeer","Bayde","Beeron","Besur","Biedgar","Bithon","Bolrock","Bredere","Breen","Buchmeid","Buthomar","Baduk","Barkydle","Beck","Bein","Besurlde","Bildon","Boal","Brakdern","Bredin","Brighton","Bue","Bydern",
"Caelholdt","Camchak","Casden","Celorn","Cerdern","Cevelt","Chidak","Ciroc","Connell","Cosdeer","Cydare","Cyton","Cainon","Camilde","Cayold","Celthric","Cespar","Chamon","Cibrock","Codern","Cordale","Cuparun","Cylmar","Calden","Cardon","Celbahr","Cemark","Cether","Chesmarn","Cipyar","Colthan","Cos","Cusmirk","Cythnar",
"Daburn","Dakamon","Dalmarn","Darkkon","Darmor","Dask","Derik","Dessfar","Doceon","Dorn","Drakone","Dritz","Dryn","Duran","Dyfar","Daermod","Dakkone","Dapvhir","Darko","Darpick","Deathmar","Derrin","Dinfar","Dochrohan","Dosoman","Drandon","Drophar","Duba","Durmark","Dyten","Dak","Dalburn","Darkboon","Darkspur","Dasbeck","Defearon","Desil","Dismer","Dokoran","Drakoe","Drit","Dryden","Dukran","Dusaro",
"Eard","Efar","Ekgamut","Elson","Endor","Enro","Eritai","Etar","Ethen","Eythil","Eckard","Egmardern","Eli","Elthin","Enidin","Erikarn","Escariet","Etburn","Etmere","Efamar","Eiridan","Elik","Enbane","Enoon","Erim","Espardo","Etdar","Etran",
"Faoturk","Fenrirr","Ficadon","Firedorn","Folmard","Fydar","Faowind","Fetmar","Fickfylo","Firiro","Fraderk","Fyn","Fearlock","Feturn","Fildon","Floran","Fronar",
"Gafolern","Galiron","Gemardt","Gerirr","Gibolock","Gom","Gothikar","Gryn","Guthale","Gyin","Gai","Gametris","Gemedern","Geth","Gibolt","Gosford","Gresforn","Gundir","Gybol","Galain","Gauthus","Gemedes","Gib","Gith","Gothar","Grimie","Gustov","Gybrush",
"Halmar","Hectar","Hermenze","Hildale","Hydale","Harrenhal","Hecton","Hermuck","Hildar","Hyten","Hasten","Heramon","Hezak","Hileict",
"Iarmod","Ieserk","Illilorn","Ipedorn","Isen","Jackson","Janus","Jesco","Jex","Jin","Jun","Kafar","Keran","Kethren","Kiden","Kildarien","Kip","Kolmorn","Lackus","Lafornon","Ledale","Lephidiles","Letor","Liphanes","Ludokrin","Lurd","Macon","Marderdeen","Markdoon","Mathar","Mellamo","Meridan","Mes'ard","Mezo","Mickal","Miphates","Modric","Mufar","Mythik","Nadeer","Naphates","Nikpal","Niro","Nuthor","Nythil","O’tho","Occhi","Ohethlic","Omarn","Othelen","Padan","Peitar","Pendus","Phairdon","Phoenix","Picumar","Ponith","Prothalon","Qeisan","Quid","Qysan","Radag'mal","Rayth","Reth","Rhithin","Rikar","Ritic","Rogoth","Rydan","Ryodan","Rythern","Sabal","Samon","Scoth","Sed","Senthyril","Seryth","Setlo","Shane","Shillen","Sil'forrin","Soderman","Stenwulf","Suth","Syth","Talberon","Temilfist","Tespar","Thiltran","Tibolt","Tithan","Tolle","Tothale","Tuk","Tyden","Uerthe","Undin","Vaccon","Valynard","Vespar","Vider","Vildar","Virde","Voudim","Wak’dern","Wekmar","William","Wiltmar","Wrathran","Wyder","Xander","Xex","Y’reth","Yesirn","Zak","Zeke","Zidar","Zilocke","Zotar"
"Idon","Ikar","Illium","Irefist","Isil","Jalil","Jayco","Jespar","Jib","Juktar","Justal","Kaldar","Kesad","Kib","Kilbas","Kimdar","Kirder","Kyrad","Lacspor","Lahorn","Leit","Lerin","Lidorn","Loban","Luphildern","Zakarn","Madarlon","Mardin","Marklin","Medarin","Meowol","Merkesh","Mesophan","Michael","Migorn","Mi'talrythin","Modum","Mujarin","Mythil","Nalfar","Neowyld","Nikrolin","Noford","Nuwolf","Zerin","Ocarin","Odaren","Okar","Orin","Oxbaren","Palid","Pelphides","Perder","Phemedes","Picon","Pildoor","Poran","Puthor","Qidan","Quiss","Zigmal","Randar","Reaper","Rethik","Rhysling","Rismak","Rogeir","Rophan","Ryfar","Rysdan","Zio","Sadareen","Samot","Scythe","Sedar","Serin","Sesmidat","Shade","Shard","Silco","Silpal","Sothale","Steven","Sutlin","Sythril","Telpur","Tempist","Tessino","Tholan","Ticharol","Tobale","Tolsar","Tousba","Tuscanar","Zutar","Ugmar","Updar","Vacone","Vectomon","Vethelot","Vigoth","Vinald","Voltain","Vythethi","Walkar","Werymn","Willican","Wishane","Wraythe","Wyeth","Xavier","Xithyl","Yabaro","Yssik",
"Ironmark","Ithric","Jamik","Jaython","Jethil","Jibar","Julthor","Ieli","Kellan","Kesmon","Kibidon","Kilburn","Kinorn","Kodof","Ilgenar","Laderic","Laracal","Lephar","Lesphares","Lin","Lox","Lupin","Zecane","Mafar","Markard","Mashasen","Medin","Merdon","Mesah","Mesoton","Mick","Milo","Mitar","Mudon","Mylo","Ingel","Namorn","Nidale","Niktohal","Nothar","Nydale","Zessfar","Occelot","Odeir","Omaniron","Ospar","Xuio","Papur","Pender","Perol","Phexides","Pictal","Pixdale","Poscidion","Pyder","Quiad","Qupar","Zile","Raysdan","Resboron","Rhithik","Riandur","Riss","Rogist","Rulrindale","Ryfar","Rythen","Zoru","Safilix","Sasic","Secor","Senick","Sermak","Seth","Shadowbane","Shardo","Sildo","Sithik","Staph","Suktor","Syr","Yssith","Temil","Teslanar","Tethran","Tibers","Tilner","Tol’Solie","Toma","Towerlock","Tusdar","Zyten","Uhrd","Uther","Valkeri","Veldahar","Victor","Vilan","Vinkolt","Volux","Yepal","Wanar","Weshin","Wilte","Witfar","Wuthmon","Wyvorn","Xenil"]

PLACES = ['Adara', 'Adena', 'Adrianne', 'Alarice', 'Alvita', 'Amara', 'Ambika', 'Antonia', 'Araceli', 'Balandria', 'Basha',
'Beryl', 'Bryn', 'Callia', 'Caryssa', 'Cassandra', 'Casondrah', 'Chatha', 'Ciara', 'Cynara', 'Cytheria', 'Dabria', 'Darcei',
'Deandra', 'Deirdre', 'Delores', 'Desdomna', 'Devi', 'Dominique', 'Drucilla', 'Duvessa', 'Ebony', 'Fantine', 'Fuscienne',
'Gabi', 'Gallia', 'Hanna', 'Hedda', 'Jerica', 'Jetta', 'Joby', 'Kacila', 'Kagami', 'Kala', 'Kallie', 'Keelia', 'Kerry',
'Kerry-Ann', 'Kimberly', 'Killian', 'Kory', 'Lilith', 'Lucretia', 'Lysha', 'Mercedes', 'Mia', 'Maura', 'Perdita', 'Quella',
'Riona', 'Safiya', 'Salina', 'Severin', 'Sidonia', 'Sirena', 'Solita', 'Tempest', 'Thea', 'Treva', 'Trista', 'Vala', 'Winta']

###############################################################################
# Markov Name model
# A random name generator, by Peter Corbett
# http://www.pick.ucam.org/~ptc24/mchain.html
# This script is hereby entered into the public domain
###############################################################################
class Mdict:
    def __init__(self):
        self.d = {}

    def __getitem__(self, key):
        if key in self.d:
            return self.d[key]
        else:
            raise KeyError(key)

    def add_key(self, prefix, suffix):
        if prefix in self.d:
            self.d[prefix].append(suffix)
        else:
            self.d[prefix] = [suffix]

    def get_suffix(self, prefix):
        l = self[prefix]
        return rd.choice(l)


class MName:
    """
    A name from a Markov chain
    """
    DICT_PEOPLE = "PEOPLE_DICT"
    DICT_PLACE = "PLACE_DICT"

    def __init__(self, dict_type, chainlen=3, ):
        """
        Building the dictionary
        """
        assert 1 < chainlen < 10, "Chain length must be between 1 and 10, inclusive"
        self.mcd = Mdict()
        oldnames = []
        self.chainlen = chainlen

        dict = NAMES
        if dict_type == MName.DICT_PEOPLE:
            dict = NAMES
        elif dict_type == MName.DICT_PLACE:
            dict = PLACES

        for l in dict:
            l = l.strip()
            oldnames.append(l)
            s = " " * chainlen + l
            for n in range(0, len(l)):
                self.mcd.add_key(s[n:n + chainlen], s[n + chainlen])
            self.mcd.add_key(s[len(l):len(l) + chainlen], "\n")

    def getName(self):
        """
        New name from the Markov chain
        """
        prefix = " " * self.chainlen
        name = ""
        suffix = ""
        while True:
            suffix = self.mcd.get_suffix(prefix)
            if suffix == "\n" or len(name) > 9:
                break
            else:
                name = name + suffix
                prefix = prefix[1:] + suffix
        return name.capitalize()

    @staticmethod
    def person_name():
        return MName(MName.DICT_PEOPLE).getName()

    @staticmethod
    def place_name():
        return MName(MName.DICT_PLACE).getName()


class FieldOfView:
    RAYS = 360  # Should be 360!

    STEP = 3  # The step of for cycle. More = Faster, but large steps may
    # cause artifacts. Step 3 is great for radius 10.

    RAD = 5  # FOV radius.

    # Tables of precalculated values of sin(x / (180 / pi)) and cos(x / (180 / pi))

    SINTABLE = [
        0.00000, 0.01745, 0.03490, 0.05234, 0.06976, 0.08716, 0.10453,
        0.12187, 0.13917, 0.15643, 0.17365, 0.19081, 0.20791, 0.22495, 0.24192,
        0.25882, 0.27564, 0.29237, 0.30902, 0.32557, 0.34202, 0.35837, 0.37461,
        0.39073, 0.40674, 0.42262, 0.43837, 0.45399, 0.46947, 0.48481, 0.50000,
        0.51504, 0.52992, 0.54464, 0.55919, 0.57358, 0.58779, 0.60182, 0.61566,
        0.62932, 0.64279, 0.65606, 0.66913, 0.68200, 0.69466, 0.70711, 0.71934,
        0.73135, 0.74314, 0.75471, 0.76604, 0.77715, 0.78801, 0.79864, 0.80902,
        0.81915, 0.82904, 0.83867, 0.84805, 0.85717, 0.86603, 0.87462, 0.88295,
        0.89101, 0.89879, 0.90631, 0.91355, 0.92050, 0.92718, 0.93358, 0.93969,
        0.94552, 0.95106, 0.95630, 0.96126, 0.96593, 0.97030, 0.97437, 0.97815,
        0.98163, 0.98481, 0.98769, 0.99027, 0.99255, 0.99452, 0.99619, 0.99756,
        0.99863, 0.99939, 0.99985, 1.00000, 0.99985, 0.99939, 0.99863, 0.99756,
        0.99619, 0.99452, 0.99255, 0.99027, 0.98769, 0.98481, 0.98163, 0.97815,
        0.97437, 0.97030, 0.96593, 0.96126, 0.95630, 0.95106, 0.94552, 0.93969,
        0.93358, 0.92718, 0.92050, 0.91355, 0.90631, 0.89879, 0.89101, 0.88295,
        0.87462, 0.86603, 0.85717, 0.84805, 0.83867, 0.82904, 0.81915, 0.80902,
        0.79864, 0.78801, 0.77715, 0.76604, 0.75471, 0.74314, 0.73135, 0.71934,
        0.70711, 0.69466, 0.68200, 0.66913, 0.65606, 0.64279, 0.62932, 0.61566,
        0.60182, 0.58779, 0.57358, 0.55919, 0.54464, 0.52992, 0.51504, 0.50000,
        0.48481, 0.46947, 0.45399, 0.43837, 0.42262, 0.40674, 0.39073, 0.37461,
        0.35837, 0.34202, 0.32557, 0.30902, 0.29237, 0.27564, 0.25882, 0.24192,
        0.22495, 0.20791, 0.19081, 0.17365, 0.15643, 0.13917, 0.12187, 0.10453,
        0.08716, 0.06976, 0.05234, 0.03490, 0.01745, 0.00000, -0.01745, -0.03490,
        -0.05234, -0.06976, -0.08716, -0.10453, -0.12187, -0.13917, -0.15643,
        -0.17365, -0.19081, -0.20791, -0.22495, -0.24192, -0.25882, -0.27564,
        -0.29237, -0.30902, -0.32557, -0.34202, -0.35837, -0.37461, -0.39073,
        -0.40674, -0.42262, -0.43837, -0.45399, -0.46947, -0.48481, -0.50000,
        -0.51504, -0.52992, -0.54464, -0.55919, -0.57358, -0.58779, -0.60182,
        -0.61566, -0.62932, -0.64279, -0.65606, -0.66913, -0.68200, -0.69466,
        -0.70711, -0.71934, -0.73135, -0.74314, -0.75471, -0.76604, -0.77715,
        -0.78801, -0.79864, -0.80902, -0.81915, -0.82904, -0.83867, -0.84805,
        -0.85717, -0.86603, -0.87462, -0.88295, -0.89101, -0.89879, -0.90631,
        -0.91355, -0.92050, -0.92718, -0.93358, -0.93969, -0.94552, -0.95106,
        -0.95630, -0.96126, -0.96593, -0.97030, -0.97437, -0.97815, -0.98163,
        -0.98481, -0.98769, -0.99027, -0.99255, -0.99452, -0.99619, -0.99756,
        -0.99863, -0.99939, -0.99985, -1.00000, -0.99985, -0.99939, -0.99863,
        -0.99756, -0.99619, -0.99452, -0.99255, -0.99027, -0.98769, -0.98481,
        -0.98163, -0.97815, -0.97437, -0.97030, -0.96593, -0.96126, -0.95630,
        -0.95106, -0.94552, -0.93969, -0.93358, -0.92718, -0.92050, -0.91355,
        -0.90631, -0.89879, -0.89101, -0.88295, -0.87462, -0.86603, -0.85717,
        -0.84805, -0.83867, -0.82904, -0.81915, -0.80902, -0.79864, -0.78801,
        -0.77715, -0.76604, -0.75471, -0.74314, -0.73135, -0.71934, -0.70711,
        -0.69466, -0.68200, -0.66913, -0.65606, -0.64279, -0.62932, -0.61566,
        -0.60182, -0.58779, -0.57358, -0.55919, -0.54464, -0.52992, -0.51504,
        -0.50000, -0.48481, -0.46947, -0.45399, -0.43837, -0.42262, -0.40674,
        -0.39073, -0.37461, -0.35837, -0.34202, -0.32557, -0.30902, -0.29237,
        -0.27564, -0.25882, -0.24192, -0.22495, -0.20791, -0.19081, -0.17365,
        -0.15643, -0.13917, -0.12187, -0.10453, -0.08716, -0.06976, -0.05234,
        -0.03490, -0.01745, -0.00000
    ]

    COSTABLE = [
        1.00000, 0.99985, 0.99939, 0.99863, 0.99756, 0.99619, 0.99452,
        0.99255, 0.99027, 0.98769, 0.98481, 0.98163, 0.97815, 0.97437, 0.97030,
        0.96593, 0.96126, 0.95630, 0.95106, 0.94552, 0.93969, 0.93358, 0.92718,
        0.92050, 0.91355, 0.90631, 0.89879, 0.89101, 0.88295, 0.87462, 0.86603,
        0.85717, 0.84805, 0.83867, 0.82904, 0.81915, 0.80902, 0.79864, 0.78801,
        0.77715, 0.76604, 0.75471, 0.74314, 0.73135, 0.71934, 0.70711, 0.69466,
        0.68200, 0.66913, 0.65606, 0.64279, 0.62932, 0.61566, 0.60182, 0.58779,
        0.57358, 0.55919, 0.54464, 0.52992, 0.51504, 0.50000, 0.48481, 0.46947,
        0.45399, 0.43837, 0.42262, 0.40674, 0.39073, 0.37461, 0.35837, 0.34202,
        0.32557, 0.30902, 0.29237, 0.27564, 0.25882, 0.24192, 0.22495, 0.20791,
        0.19081, 0.17365, 0.15643, 0.13917, 0.12187, 0.10453, 0.08716, 0.06976,
        0.05234, 0.03490, 0.01745, 0.00000, -0.01745, -0.03490, -0.05234, -0.06976,
        -0.08716, -0.10453, -0.12187, -0.13917, -0.15643, -0.17365, -0.19081,
        -0.20791, -0.22495, -0.24192, -0.25882, -0.27564, -0.29237, -0.30902,
        -0.32557, -0.34202, -0.35837, -0.37461, -0.39073, -0.40674, -0.42262,
        -0.43837, -0.45399, -0.46947, -0.48481, -0.50000, -0.51504, -0.52992,
        -0.54464, -0.55919, -0.57358, -0.58779, -0.60182, -0.61566, -0.62932,
        -0.64279, -0.65606, -0.66913, -0.68200, -0.69466, -0.70711, -0.71934,
        -0.73135, -0.74314, -0.75471, -0.76604, -0.77715, -0.78801, -0.79864,
        -0.80902, -0.81915, -0.82904, -0.83867, -0.84805, -0.85717, -0.86603,
        -0.87462, -0.88295, -0.89101, -0.89879, -0.90631, -0.91355, -0.92050,
        -0.92718, -0.93358, -0.93969, -0.94552, -0.95106, -0.95630, -0.96126,
        -0.96593, -0.97030, -0.97437, -0.97815, -0.98163, -0.98481, -0.98769,
        -0.99027, -0.99255, -0.99452, -0.99619, -0.99756, -0.99863, -0.99939,
        -0.99985, -1.00000, -0.99985, -0.99939, -0.99863, -0.99756, -0.99619,
        -0.99452, -0.99255, -0.99027, -0.98769, -0.98481, -0.98163, -0.97815,
        -0.97437, -0.97030, -0.96593, -0.96126, -0.95630, -0.95106, -0.94552,
        -0.93969, -0.93358, -0.92718, -0.92050, -0.91355, -0.90631, -0.89879,
        -0.89101, -0.88295, -0.87462, -0.86603, -0.85717, -0.84805, -0.83867,
        -0.82904, -0.81915, -0.80902, -0.79864, -0.78801, -0.77715, -0.76604,
        -0.75471, -0.74314, -0.73135, -0.71934, -0.70711, -0.69466, -0.68200,
        -0.66913, -0.65606, -0.64279, -0.62932, -0.61566, -0.60182, -0.58779,
        -0.57358, -0.55919, -0.54464, -0.52992, -0.51504, -0.50000, -0.48481,
        -0.46947, -0.45399, -0.43837, -0.42262, -0.40674, -0.39073, -0.37461,
        -0.35837, -0.34202, -0.32557, -0.30902, -0.29237, -0.27564, -0.25882,
        -0.24192, -0.22495, -0.20791, -0.19081, -0.17365, -0.15643, -0.13917,
        -0.12187, -0.10453, -0.08716, -0.06976, -0.05234, -0.03490, -0.01745,
        -0.00000, 0.01745, 0.03490, 0.05234, 0.06976, 0.08716, 0.10453, 0.12187,
        0.13917, 0.15643, 0.17365, 0.19081, 0.20791, 0.22495, 0.24192, 0.25882,
        0.27564, 0.29237, 0.30902, 0.32557, 0.34202, 0.35837, 0.37461, 0.39073,
        0.40674, 0.42262, 0.43837, 0.45399, 0.46947, 0.48481, 0.50000, 0.51504,
        0.52992, 0.54464, 0.55919, 0.57358, 0.58779, 0.60182, 0.61566, 0.62932,
        0.64279, 0.65606, 0.66913, 0.68200, 0.69466, 0.70711, 0.71934, 0.73135,
        0.74314, 0.75471, 0.76604, 0.77715, 0.78801, 0.79864, 0.80902, 0.81915,
        0.82904, 0.83867, 0.84805, 0.85717, 0.86603, 0.87462, 0.88295, 0.89101,
        0.89879, 0.90631, 0.91355, 0.92050, 0.92718, 0.93358, 0.93969, 0.94552,
        0.95106, 0.95630, 0.96126, 0.96593, 0.97030, 0.97437, 0.97815, 0.98163,
        0.98481, 0.98769, 0.99027, 0.99255, 0.99452, 0.99619, 0.99756, 0.99863,
        0.99939, 0.99985, 1.00000
    ]

    @staticmethod
    def get_vision_matrix_for(entity, region, radius=RAD, flag_explored=False, ignore_entity_at=None):
        """
        The Field of View algo
        :param entity: the entity for which the algo is done
        :param radius: the number of tiles the user can go throught
        :param flag_explored: any unexplored tile will become explored (good for player, but not NPC)
        :param ignore_entity_at: will ignore any entity at positions (like player) - this is a list
        :return: the Field of view, with True for each tile that is visible
        """
        fov = [[False for y in range(region.tile_height)] for x in
               range(region.tile_width)]

        # It works like this:
        # It starts at entity coordinates and cast 360 rays
        # (if step is 1, less is step is more than 1) in every direction,
        # until it hits a wall.
        # When ray hits floor, it is set as visible.

        # Ray is casted by adding to x (initialy it is player's x coord)
        # value of sin(i degrees) and to y (player's y) value of cos(i degrees),
        # RAD times, and checking for collision with wall every step.

        # First: the entity itself is visible!
        fov[entity.x][entity.y] = True  # Make tile visible
        if flag_explored:
            region.tiles[entity.x][entity.y].explored = True

        for i in range(0, FieldOfView.RAYS + 1, FieldOfView.STEP):
            ax = FieldOfView.SINTABLE[i]  # Get precalculated value sin(x / (180 / pi))
            ay = FieldOfView.COSTABLE[i]  # cos(x / (180 / pi))

            x = entity.x  # Entity x
            y = entity.y  # Entity y

            for z in range(radius):  # Cast the ray
                x += ax
                y += ay

                round_x = int(round(x))
                round_y = int(round(y))
                if round_x < 0 or round_y < 0 or round_x > region.tile_width or \
                                round_y > region.tile_height:  # Ray is out of range
                    break

                fov[round_x][round_y] = True  # Make tile visible
                if flag_explored:
                    region.tiles[round_x][round_y].explored = True
                if ignore_entity_at is not None:
                    if (round_x, round_y) not in ignore_entity_at and \
                            region.tiles[round_x][round_y].block_view_for(entity):
                        break
                elif region.tiles[round_x][round_y].block_view_for(entity):  # Stop ray if it hit
                    break

        return fov

# Graphical utilities
def get_image(image_src_list, folder, image_name):
    key = str(folder) + image_name
    if key not in image_src_list:
        image_src_list[key] = pg.image.load(os.path.join(folder, image_name)).convert_alpha()
    return image_src_list[key]


def load_image(image_src_list, folder, image_name, tile_x, tile_y, width=16, height=16, adapt_ratio=1):
    """
    Load a single image from a file and put it in the image dictionnary
    :param image_src_list: the image dictionnary that will be modified
    :param folder: the folder from which the image needs to be loaded
    :param image_name: the name of the file to be loaded
    :param tile_x: the position in the file of the sub part to be loaded (x)
    :param tile_y: the position in the file of the sub part to be loaded (y)
    :param width: the dimension of a tile
    :param height: th edimension of a tile
    :return:
    """
    image_src = get_image(image_src_list, folder, image_name)
    if adapt_ratio is None:
        return image_src.subsurface(pg.Rect(width * tile_x, height * tile_y, width, height))
    elif width == TILESIZE_SCREEN[0] * adapt_ratio and height == TILESIZE_SCREEN[1] * adapt_ratio:
        return image_src.subsurface(pg.Rect(width * tile_x, height * tile_y, width, height))
    else:
        return pg.transform.scale(image_src.subsurface(pg.Rect(width * tile_x, height * tile_y, width, height)),
                                  (int(TILESIZE_SCREEN[0] * adapt_ratio), int(TILESIZE_SCREEN[1] * adapt_ratio)))


def load_image_list_dawnlike(image_src_list, folder, image_name1, image_name2, tile_x, tile_y,
                             width=16, height=16):
    """
    Load an image list from two different files following dawnlike approach
    :param image_src_list: the actual dictionary that may already contain the source
    :param img_folder_name: the folder where images are located
    :param image1: the first image file name
    :param image2: the second image file name
    :param tile_x: th etile position - note that
    :param tile_y:
    :param width:
    :param height:
    :return: a list of two images
    """
    image_src1 = get_image(image_src_list, folder, image_name1)
    image_src2 = get_image(image_src_list, folder, image_name2)

    if width == TILESIZE_SCREEN[0] and height == TILESIZE_SCREEN[1]:
        return [image_src1.subsurface(pg.Rect(width * tile_x, height * tile_y, width, height)),
                image_src2.subsurface(pg.Rect(width * tile_x, height * tile_y, width, height))]
    else:
        return [pg.transform.scale(image_src1.subsurface(pg.Rect(width * tile_x, height * tile_y, width, height)),
                                   TILESIZE_SCREEN),
                pg.transform.scale(image_src2.subsurface(pg.Rect(width * tile_x, height * tile_y, width, height)),
                                   TILESIZE_SCREEN)]


def load_wall_structure_dawnlike(image_src_list, folder, image_name):
    """
    Load the set of walls from dawnlike file
    :param image_src_list: the actual dictionary that may already contain the source
    :param image_src:
    :return: a list of dictionary item following convention
    http://www.angryfishstudios.com/2011/04/adventures-in-bitmasking/
    """
    image_src = get_image(image_src_list, folder, image_name)
    image_set = []
    ref_tuples = {0: (1, 1), 1: (1, 1),
                  2: (1, 0), 3: (0, 2),
                  4: (0, 1), 5: (0, 1),
                  6: (0, 0), 7: (3, 1),
                  8: (1, 0), 9: (2, 2),
                  10: (1, 0), 11: (4, 2),
                  12: (2, 0), 13: (5, 1),
                  14: (4, 0), 15: (4, 1)}
    for line in range(16):
        for column in range(2):
            top_x = column * (7 * 16)
            top_y = line * (3 * 16) + 3 * 16
            dict_image = {}
            for key in ref_tuples:
                delta_x = ref_tuples[key][0] * 16 + top_x
                delta_y = ref_tuples[key][1] * 16 + top_y
                dict_image[key] = pg.transform.scale(image_src.subsurface(pg.Rect(delta_x, delta_y, 16, 16)),
                                                     TILESIZE_SCREEN)
            image_set.append(dict_image)
    return image_set


def load_floor_structure_dawnlike(image_src_list, folder, image_name):
    """
    Load the set of walls from dawnlike file and put it in a dictionary
    :param image_src_list: the actual dictionary that may already contain the source
    :param folder: the folder from which the image will be loaded
    :param the name of teh image file
    :return: a list of dictionary item following convention
    http://www.angryfishstudios.com/2011/04/adventures-in-bitmasking/
    """
    image_src = get_image(image_src_list, folder, image_name)
    image_set = []
    ref_tuples = {0: (5, 0), 1: (3, 2),
                  2: (4, 1), 3: (0, 2),
                  4: (3, 0), 5: (3, 1),
                  6: (0, 0), 7: (0, 1),
                  8: (6, 1), 9: (2, 2),
                  10: (5, 1), 11: (1, 2),
                  12: (2, 0), 13: (2, 1),
                  14: (1, 0), 15: (1, 1)}
    for line in range(8):
        for column in range(3):
            top_x = column * (7 * 16)
            top_y = line * (3 * 16) + 3 * 16
            dict_image = {}
            for key in ref_tuples:
                delta_x = ref_tuples[key][0] * 16 + top_x
                delta_y = ref_tuples[key][1] * 16 + top_y
                dict_image[key] = pg.transform.scale(image_src.subsurface(pg.Rect(delta_x, delta_y, 16, 16)),
                                                     TILESIZE_SCREEN)
            image_set.append(dict_image)
    return image_set

def load_tree_structure_dawnlike(image_src_list, folder, image_name):
    """
    Load the set of walls from dawnlike file and put it in a dictionary
    :param image_src_list: the actual dictionary that may already contain the source
    :param folder: the folder from which the image will be loaded
    :param the name of teh image file
    :return: a list of dictionary item following convention
    http://www.angryfishstudios.com/2011/04/adventures-in-bitmasking/
    """
    image_src = get_image(image_src_list, folder, image_name)
    image_set = []

    ref_tuples = {0: (3, 0), 1: (1, 2),
                  2: (0, 1), 3: (5, 0),
                  4: (1, 0), 5: (3, 0),
                  6: (5, 1), 7: (0, 1),
                  8: (2, 1), 9: (4, 0),
                  10: (3, 0), 11: (1, 2),
                  12: (4, 1), 13: (2, 1),
                  14: (1, 0), 15: (1, 1)}
    for line in range(11):
        for column in range(2):
            top_x = column * (6 * 16)
            top_y = line * (3 * 16) + 3 * 16
            dict_image = {}
            for key in ref_tuples:
                delta_x = ref_tuples[key][0] * 16 + top_x
                delta_y = ref_tuples[key][1] * 16 + top_y
                dict_image[key] = pg.transform.scale(image_src.subsurface(pg.Rect(delta_x, delta_y, 16, 16)),
                                                     TILESIZE_SCREEN)
            image_set.append(dict_image)
    return image_set


def _load_player(image_src_list, folder, image_name, width=16, height=16):
    result = {"S": [load_image(image_src_list, folder, image_name, i, 0, width=width, height=height) for i in range(4)],
              "W": [load_image(image_src_list, folder, image_name, i, 1, width=width, height=height) for i in range(4)],
              "E": [load_image(image_src_list, folder, image_name, i, 2, width=width, height=height) for i in range(4)],
              "N": [load_image(image_src_list, folder, image_name, i, 3, width=width, height=height) for i in range(4)]}
    return result


def load_all_images():

    images = {}  # the actual list of images to be built
    image_src_list = {}  # a cache for objects

    # Folder: Player
    images["PLAYER_ENGINEER"] = _load_player(image_src_list, PLAYER_FOLDER, "Engineer.png")
    images["PLAYER_MAGE"] = _load_player(image_src_list, PLAYER_FOLDER, "Mage.png")
    images["PLAYER_PALADIN"] = _load_player(image_src_list, PLAYER_FOLDER, "Paladin.png")
    images["PLAYER_ROGUE"] = _load_player(image_src_list, PLAYER_FOLDER, "Rogue.png")
    images["PLAYER_WARRIOR"] = _load_player(image_src_list, PLAYER_FOLDER, "Warrior.png")

    # Folder: Objects
    # Floor & Wall
    images["FLOOR"] = load_floor_structure_dawnlike(image_src_list, OBJECT_FOLDER, "Floor.png")
    images["WALLS"] = load_wall_structure_dawnlike(image_src_list, OBJECT_FOLDER, "Wall.png")
    images["TREES"] = load_tree_structure_dawnlike(image_src_list, OBJECT_FOLDER, "Tree0.png")

    # Doors
    images["DOOR_V_OPEN"] = load_image(image_src_list, OBJECT_FOLDER, "Door1.png", 0, 0)
    images["DOOR_V_CLOSED"] = load_image(image_src_list, OBJECT_FOLDER, "Door0.png", 0, 0)
    images["DOOR_H_OPEN"] = load_image(image_src_list, OBJECT_FOLDER, "Door1.png", 1, 0)
    images["DOOR_H_CLOSED"] = load_image(image_src_list, OBJECT_FOLDER, "Door0.png", 1, 0)
    # Stairs
    images["STAIRS"] = load_image(image_src_list, OBJECT_FOLDER, "Tile.png", 1, 1)
    # Town
    images["TOWN"] = load_image(image_src_list, OBJECT_FOLDER, "Map0.png", 9, 12)

    # Buildings
    images["BUILDING_BANK"] = load_image(image_src_list, ICON_FOLDER, "bank.png", 0, 0, width=64, height=64)
    images["BUILDING_GUILD_FIGHTER"] = load_image(image_src_list, ICON_FOLDER, "guild-fighter.png", 0, 0, width=64,
                                                  height=64)
    images["BUILDING_GUILD_MULE"] = load_image(image_src_list, ICON_FOLDER, "guild-mule.png", 0, 0, width=64,
                                               height=64)
    images["BUILDING_SHOP"] = load_image(image_src_list, ICON_FOLDER, "shop.png", 0, 0, width=64, height=64)
    images["BUILDING_TAVERN"] = load_image(image_src_list, ICON_FOLDER, "tavern.png", 0, 0, width=64, height=64)
    images["BUILDING_TEMPLE"] = load_image(image_src_list, ICON_FOLDER, "temple.png", 0, 0, width=64, height=64)
    images["BUILDING_TOWNHALL"] = load_image(image_src_list, ICON_FOLDER, "townhall.png", 0, 0, width=64, height=64)
    images["BUILDING_TRADE"] = load_image(image_src_list, ICON_FOLDER, "trade.png", 0, 0, width=64, height=64)
    images["BUILDING_ENTRANCE"] = load_image(image_src_list, ICON_FOLDER, "entrance.png", 0, 0, width=64, height=64)
    
    return images
