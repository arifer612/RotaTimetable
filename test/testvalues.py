from tests.rtt import Role, Personnel, Vehicle, Appliance, Rota, Station


# Generate the station object
stn = Station('stn')

# Creates a rota in the station
r = stn.rota('rr')

# Generate roles
FF = stn.role('FF')
SC = stn.role('SC', inherit=FF)
PO = stn.role('PO', inherit=SC)
DRC = stn.role('DRC', inherit=PO)
RC = stn.role('RC', inherit=PO)

# Generate appliances
PL = stn.appliance('PL', {DRC:1, PO:1, SC:1, FF:4})
LF = stn.appliance('LF', {PO:1, SC:1, FF:2})

# Generate vehicles
PL551 = stn.vehicle('PL551', PL, 'YK1111')
LF551 = stn.vehicle('LF551', LF, 'GK1112')

# Generate personnel
rc = r.personnel('rc', RC)
drc = r.personnel('drc', DRC)
po1 = r.personnel('po1', PO)
po2 = r.personnel('po2', PO)
po3 = r.personnel('po3', PO)
po4 = r.personnel('po4', PO)
sc1 = r.personnel('sc1', SC)
sc2 = r.personnel('sc2', SC)
sc3 = r.personnel('sc3', SC)
sc4 = r.personnel('sc4', SC)
ff1 = r.personnel('ff1', FF)
ff2 = r.personnel('ff2', FF)
