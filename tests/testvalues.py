from tests import Role, Personnel, Vehicle, Appliance, Rota, Station


# Generate the station object
stn = Station('stn')

# Creates a rota in the station
r = stn.rota('rr')

# Generate roles
role = stn.role
FF = role('FF')
SC = role('SC', inherit=FF)
PO = role('PO', inherit=SC)
DRC = role('DRC', inherit=PO)
RC = role('RC', inherit=PO)

# Generate appliances
appliance = stn.appliance
PL = appliance('PL', {DRC:1, PO:1, SC:1, FF:4})
LF = appliance('LF', {PO:1, SC:1, FF:2})

# Generate vehicles
vehicle = stn.vehicle
PL551 = vehicle('PL551', PL, 'YK1111')
LF551 = vehicle('LF551', LF, 'GK1112')

# Generate personnel
p = r.personnel
rc = r('rc', RC)
drc = r('drc', DRC)
po1 = r('po1', PO)
po2 = r('po2', PO)
po3 = r('po3', PO)
po4 = r('po4', PO)
sc1 = r('sc1', SC)
sc2 = r('sc2', SC)
sc3 = r('sc3', SC)
sc4 = r('sc4', SC)
ff1 = r('ff1', FF)
ff2 = r('ff2', FF)


