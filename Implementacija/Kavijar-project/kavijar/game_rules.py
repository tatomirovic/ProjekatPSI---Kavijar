#Autor: Konstantin Jaredic

import math, datetime, random

from .models import City, Building, Army
from . import db

goldPerHour = 3
woodPerHour = 1
stonePerHour = 1

timescaler = 0.1

startingPopulation = 250
startingGold = 300
startingWood = 400
startingStone = 400

distance_mult = 100.0

# SVI MOGUCI TIPOVI ZGRADA
building_types = {
    'TH': 'Gradska uprava',
    'PI': 'Pilana',
    'KL': 'Kamenolom',
    'TS': 'Trgovinska stanica',
    'BP': 'Baraka za pešadiju',
    'BK': 'Baraka za konjicu',
    'BS': 'Baraka za strelce',
    'BO': 'Radionica opsadnog oružja',
    'ZD': 'Zidine'
}

# SVI MOGUCI TIPOVI JEDINICA
unit_types = {
    'LP': 'Laka pešadija',
    'TP': 'Teška pešadija',
    'ST': 'Strelci',
    'SS': 'Samostrelci',
    'LK': 'Laka konjica',
    'TK': 'Teška konjica',
    'KT': 'Katapulti',
    'TR': 'Trebušeti'
}

# TESKE JEDINICE - NEOPHODNO JER SE RAZLIKUJU OD OBICNIH PRI REGRUTOVANJU
heavy_unit_types = ['TP', 'SS', 'TK', 'TR']

# OVAKO POVEZUJEMO OZNAKE JEDINICA I SQL POLJA ZA NJIH
unit_type_fields = {
    'LP': 'lakaPesadija',
    'TP': 'teskaPesadija',
    'ST': 'strelci',
    'SS': 'samostrelci',
    'LK': 'lakaKonjica',
    'TK': 'teskaKonjica',
    'KT': 'katapult',
    'TR': 'trebuset'
}

# OSNOVNE CENE UNAPREDJENJA ZGRADA
building_costs = {
    'TH': {'gold': 500, 'wood': 300, 'stone': 600},
    'PI': {'gold': 130, 'wood': 0, 'stone': 250},
    'KL': {'gold': 30, 'wood': 100, 'stone': 250},
    'TS': {'gold': 200, 'wood': 200, 'stone': 200},
    'BP': {'gold': 70, 'wood': 100, 'stone': 150},
    'BK': {'gold': 150, 'wood': 100, 'stone': 150},
    'BS': {'gold': 100, 'wood': 100, 'stone': 150},
    'BO': {'gold': 300, 'wood': 500, 'stone': 150},
    'ZD': {'gold': 50, 'wood': 100, 'stone': 500}
}

# POVEZUJE JEDINICU SA BARAKOM ZADUZENOM ZA NJU
barracks_allocation = {
    'LP': 'BP',
    'TP': 'BP',
    'ST': 'BS',
    'SS': 'BS',
    'LK': 'BK',
    'TK': 'BK',
    'KT': 'BO',
    'TR': 'BO'
}

# MAX RESURSA KOJE MOZES IMATI PRI ODREDJENOM LVLU
resource_caps = {
    0: 1000,
    1: 15000,
    2: 50000,
    3: 100000,
    4: 250000,
    5: 10000000
}

# MAX RADNIKA KOJE MOZES ZADUZITI ZA NEKI RESURS PO ODREDJENOM LVLU ZGRADE
resource_allocation_limit = {
    0: 100,
    1: 250,
    2: 10000,
    3: 50000,
    4: 250000,
    5: 1000000
}

# SKALIRANJE CENE UPGRADE-A ZAGRADE U ZAVISNOSTI OD NIVOA. NEGATIVNO JER SE ODUZIMA OD IGRACEVIH RESURSA
building_costs_scaling = {
    0: 0,
    1: -1,
    2: -3,
    3: -10,
    4: -20,
    5: -100,
}

# SKALIRANJE VREMENA UPGRADE-A ZAGRADE U ZAVISNOSTI OD NIVOA U MINUTIMA
building_build_time_scaling = [0, 5, 20, 60, 300, 1440]

# SKALIRANJE BRZINE REGRUTOVANJE U ZAVISNOSTI OD NIVOA BARAKE
barracks_recruit_time_scaling = [0, 1, 5, 10, 15, 20]


# KOLIKO KOSTA RESURSA JEDNA INSTANCA JEDINICE
unit_costs = {
    "LP": {'gold': 30, 'wood': 0, 'stone': 0, 'population': 1},
    "TP": {'gold': 60, 'wood': 0, 'stone': 0, 'population': 1},
    "ST": {'gold': 20, 'wood': 10, 'stone': 0, 'population': 1},
    "SS": {'gold': 45, 'wood': 15, 'stone': 0, 'population': 1},
    "LK": {'gold': 70, 'wood': 0, 'stone': 0, 'population': 2},
    "TK": {'gold': 100, 'wood': 0, 'stone': 0, 'population': 3},
    "KT": {'gold': 100, 'wood': 50, 'stone': 20, 'population': 1},
    "TR": {'gold': 250, 'wood': 80, 'stone': 40, 'population': 1},
}

# KOLIKO VREMENA TREBA DA SE REGRUTUJE JEDNA JEDINICA
unit_recruit_times = {
    "LP": 5,
    "TP": 10,
    "ST": 5,
    "SS": 10,
    "LK": 20,
    "TK": 40,
    "KT": 50,
    "TR": 100,
}

# MAX RESURSA U JEDNOJ PONUDI PRI TRGOVANJU
tp_resource_cap = {
    0: 0,
    1: 100,
    2: 5000,
    3: 10000,
    4: 50000,
    5: 200000
}

# KOLIKO SE RESURSA REFUNDIRA AKO SE OTKAZE IZGRADNJA
refund_mult = -0.5

# MAX LVL ZGRADE
building_max_level = 5

# VRACA DICT SA CENOM UPGRADE-A ZA DATU ZGRADU
def build_cost(bType, level):
    costdict = {'gold': 0, 'wood': 0, 'stone': 0}
    if level > building_max_level:
        level = building_max_level
    for k in costdict.keys():
        costdict[k] = building_costs[bType][k] * building_costs_scaling[level]
    return costdict


# VRACA BROJ SEKUNDI POTREBNIH ZA UPDATE
def build_time(level, b_type):
    return timescaler * building_build_time_scaling[level]


# VRACA CENU REGRUTOVANJE TE KOLICINE JEDINICA KAO DICT
def recruit_cost(uType, quantity):
    costdict = {'gold': 0, 'wood': 0, 'stone': 0, 'population': 0}
    for k in costdict.keys():
        costdict[k] = unit_costs[uType][k] * quantity
    return costdict


def recruit_time_seconds(uType, quantity, barracks_level):
    return (60.0 * timescaler * quantity * unit_recruit_times[uType]) / barracks_recruit_time_scaling[barracks_level]


# BITNO - POZVATI db.session.commit() POSLE OVE FUNKCIJE, NE POZIVA GA SAMA
# POZIVATI OVU F-JU PRE SVAKOG AZURIRANJA RESURSA
def adjust_resources(player, gold=0, wood=0, stone=0, pop=0, kavijar=0, debug=False, context=''):
    city = City.query.filter_by(idOwner=player.idUser).first()
    if city is None:
        return
    if debug:
        #print(f'Adjusting resources for Player: {player.username}, G: {gold} W: {wood} S: {stone}, context is {context}')
        pass
    city.gold += gold
    city.wood += wood
    city.stone += stone
    city.population += pop
    player.caviar += kavijar
    th_level = Building.query.filter_by(idCity=city.idCity, type="TH").first().level
    rcap = resource_caps[th_level]
    if city.gold > rcap:
        city.gold = rcap
    if city.wood > rcap:
        city.wood = rcap
    if city.stone > rcap:
        city.stone = rcap
    if city.gold < 0:
        city.gold = 0
    if city.wood < 0:
        city.wood = 0
    if city.stone < 0:
        city.stone = 0
    if city.population < startingPopulation:
        city.population = startingPopulation


# KREIRA POCETNI GARNIZON SVAKOG GRADA
def createGarrison(idCity):
    db.session.add(
        Army(idCityFrom=idCity, status="G", lakaPesadija=0, teskaPesadija=0, lakaKonjica=0, teskaKonjica=0, strelci=0,
             samostrelci=0, katapult=0, trebuset=0))
    db.session.commit()


# FUNKCIJA ZA CENTRIRANJE GRADOVA
def normalCap(D=30):
    x = random.gauss(D / 2, D / 6)
    if x < 1: return 1
    if x > D: return D
    return int(x)


# FUNKCIJA KOJA KREIRA GRAD
def createCity(idOwner, name):
    xCoord = 0
    yCoord = 0
    cities = City.query.all()
    while True:
        xCoord = normalCap()
        yCoord = normalCap()
        for city in cities:
            dist = (city.xCoord - xCoord) ** 2 + (city.yCoord - yCoord) ** 2
            if dist < 4:
                break
        else:
            break

    db.session.add(City(idOwner=idOwner, name=name, xCoord=xCoord, yCoord=yCoord, population=startingPopulation,
                        woodworkers=0, stoneworkers=0, civilians=startingPopulation, gold=startingGold,
                        wood=startingWood, stone=startingStone, lastUpdate=datetime.datetime.now()))
    db.session.commit()

    idCity = City.query.filter_by(idOwner=idOwner, name=name).first().idCity
    #createTownHall(idCity)
    for k in building_types.keys():
        new_building = Building(idCity=idCity, type=k, status="A", level=0, finishTime=datetime.datetime.now())
        if new_building.type in ['TH', 'PI', 'KL']:
            new_building.level = 1
        db.session.add(new_building)
    createGarrison(idCity)


carry_capacity = [1000, 5000, 20000, 50000, 100000]
growth_rate = 0.1


# FUNKCIJA KOJA IZRACUNAVA EKSPONENCIJALNI RAST POPULACIJE
def growth(p0, dt, townHallLevel):
    k = carry_capacity[townHallLevel - 1]
    r = growth_rate
    return k / (1 + (k - p0) / p0 * math.exp(-r * dt / timescaler))


# VRACA RAZDALJINU IZMEDJU 2 GRADA
def cityDistance(city1, city2):
    return ((city1.xCoord - city2.xCoord) ** 2 + (city1.yCoord - city2.yCoord) ** 2) ** .5

# VRACA VREME PUTOVANJA IZMEDJU 2 GRADA U SEKUNDAMA
def cityTravelTime_seconds(city1, city2):
    return distance_mult * cityDistance(city1, city2) * timescaler
