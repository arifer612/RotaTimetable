# -*- coding: utf-8 -*-
"""
Created on Fri Sep 18 23:38:27 2020

Script to manage turnouts every shift

@author: Arif Er
"""

import pickle
import os
import sys
import hashlib
from typing import Union


class Role(object):
    def __init__(self, name,
                 constraint: Union[dict, list, str] = None, rule: bool = False,
                 inherit: "Role" = None):
        self.role, self._constraints, self._inheritance = name, {}, inherit

        if type(rule) is not bool:
            raise TypeError("Only boolean rules are allowed")

        if inherit:
            if not isinstance(inherit, Role):
                raise TypeError("Only <Role> can be inherited")

        if constraint:
            if type(constraint) is dict:
                for i, j in constraint:
                    if type(i) is not "Vehicle":
                        raise TypeError("Only <Vehicle> can be added as constraints")
                    if type(j) is not bool:
                        raise TypeError("Only <boolean> rules are allowed")
                    self._constraints.update(constraint)
            elif type(constraint) is list:
                self._constraints.update({i: rule for i in constraint})
            else:
                self._constraints.update({constraint: rule})

    @property
    def constraints(self):
        if self._inheritance:
            return {**self._inheritance.constraints, **self._constraints}
        else:
            return self._constraints

    def constraint(self, constraint=None, rule=False):
        if constraint:
            self._constraints.update({constraint: rule})

    def __add__(self, other):
        if type(other) is not Role:
            print(type(other))
            raise TypeError("Only <Role> can be added to <Role>")
        else:
            if other.constraints:
                for constraint, rule in other.constraints.items():
                    if constraint not in self.constraints:
                        self.constraint(constraint, rule)
            else:
                pass

    def __repr__(self):
        return self.role

    def __str__(self):
        return f"{self.constraints if self.constraints else 'NONE'}"


class Personnel(Role):
    def __init__(self, name, role=None):
        self._name = name
        super().__init__(role)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, newName):
        self._name = newName

    @property
    def id(self):
        return hashlib.sha1(f"{self.name} @ {self.role}".encode()).hexdigest()

    @property
    def constraints(self):
        return self.role.constraints

    def __repr__(self):
        return self.id

    def __str__(self):
        return self.name

    def __call__(self):
        return {
            'name': self.name,
            'role': self.role,
            'constraints': self.constraints
        }


class Appliance(object):
    def __init__(self, name, crew, minimum=1, maximum=1):
        if not crew:
            raise ValueError(f"Assign minimum crew of {name}")
        elif type(crew) is not dict:
            raise TypeError("Crew has to be represented as a dictionary")
        if maximum < minimum:
            raise ValueError(f"Maximum cannot be less than the minimum")
        maximum = maximum if maximum >= sum(crew.values()) else sum(crew.values())

        self._appliance, self._crew, self.limits = name, crew, [minimum, maximum]

    @property
    def appliance(self):
        return self._appliance

    @appliance.setter
    def appliance(self, newName):
        self._appliance = newName

    @property
    def crew(self):
        self._crew = {i: v for (i, v) in self._crew.items() if v}
        return self._crew

    def __repr__(self):
        return f"{self.crew}"

    def change(self, role, value=None, maximum=None):
        self.limits[1] = maximum
        crew = self.crew
        if type(role) is dict:
            for i, j in role.items():
                if type(j) is not int:
                    raise TypeError("Only integer values are allowed")
            crew.update(role)
            if sum(crew.values()) > self.limits[1]:
                raise ValueError("Total crew exceeds maximum of the appliance")
            else:
                self._crew.update(role)
        elif not value:
            raise AttributeError(f"Number of {role} has to be declared")
        elif type(value) is not int:
            raise TypeError("Only integer values are allowed")
        else:
            crew.update({role: value})
            if sum(crew.values()) > self.limits[1]:
                raise ValueError("Total crew exceeds maximum of the appliance")
            else:
                self._crew.update({role: value})


class Vehicle(Appliance):
    def __init__(self, callsign, appliance: Appliance, plateNumber, active: bool = True):
        if type(appliance) is not Appliance:
            raise TypeError(f"{appliance} is not an Appliance. Create the object first")
        self._callsign, self._plateNumber, self._active = callsign, plateNumber, active
        super().__init__(appliance.appliance, appliance.crew, *appliance.limits)

    @property
    def callsign(self):
        return self._callsign

    @callsign.setter
    def callsign(self, newCallsign):
        self._callsign = newCallsign

    @property
    def plate(self):
        return self._plateNumber

    @property
    def active(self):
        return self._active

    @active.setter
    def active(self, val: bool):
        if type(val) is not bool:
            raise TypeError("Only boolean values are allowed")
        self._active = val

    @plate.setter
    def plate(self, newPlate):
        self._plateNumber = newPlate

    def onRun(self):
        self.active = True

    def offRun(self):
        self.active = False

    def __repr__(self):
        return f"{self.callsign} ({self.plate}) -- {'On run' if self.active else 'Off run'}"

    def __call__(self):
        return {
            'callsign': self.callsign
        }


def safeLoad(function):
    def runFunction(self, *args, **kwargs):
        self._load()
        function(self, *args, **kwargs)
        self._save()

    return runFunction


class Rota(object):
    def __init__(self, fileName=None, rootDir=".", rota: int = None):
        if not (rota or fileName):
            sys.exit('Provide rota number to create a new rota or log file directory to load data')
        else:
            self.rota, self._fileName, self._rootDir = rota, fileName, rootDir
            self._personnel, self._appliances = [], []
            if not self._fileName:
                if not rota:
                    raise NameError("Declare rota number to create a new rota")
                self._fileName = f"Rota {self.rota}.data"
                self._rootDir = rootDir
            self._load()

    @property
    def personnel(self):
        return self._personnel

    @property
    def _personnelID(self):
        return {i.id[:8]: i for i in self._personnel}

    @property
    def appliances(self):
        return self._appliances

    @property
    def _callsigns(self):
        return {i.callsign: i for i in self._appliances}

    @property
    def active(self):
        return [i for i in self.appliances if i.active]

    def __call__(self, arg=None):
        if arg:
            if type(arg) is Personnel or Vehicle:
                return arg
            elif type(arg) is str:
                if arg in self._personnelID:
                    return self._personnelID[arg]
                elif arg in self._callsigns:
                    return self._callsigns[arg]
                else:
                    print(f"{arg} does not exist in this rota")
        else:
            return {
                'rota': self.rota,
                'personnel': self.personnel,
                'appliances': self.appliances
            }

    @safeLoad
    def __add__(self, other):
        if type(other) is Rota:
            self._personnel = list(set(self.personnel) | set(other.personnel))
            self._appliances = list(set(self.appliances) | set(other.appliances))
        elif type(other) is Personnel:
            if other.id[:8] not in self._personnelID:
                self._personnel.append(other)
        elif type(other) is Vehicle:
            if other.callsign not in self._callsigns:
                self._appliances.append(other)
        else:
            raise TypeError(f"{type(other)} cannot be operated on <Rota>")

    @safeLoad
    def __sub__(self, other):
        if type(other) is Rota:
            self._personnel = list(set(self.personnel) - set(other.personnel))
            self._appliances = list(set(self.appliances) - set(other.appliances))
        elif type(other) is Personnel:
            if other.id[:8] in self._personnelID:
                self._personnel.pop(list(self._personnelID).index(other.id[:8]))
        elif type(other) is Appliance:
            if other.callsign in self._callsigns:
                self._appliances.pop(list(self._callsigns).index(other.callsign))
        else:
            raise TypeError(f"{type(other)} cannot be operated on <Rota>")

    def add(self, other):
        if type(other) is not list:
            other = [other]
        [self + i for i in other]

    def sub(self, other):
        if type(other) is not list:
            other = [other]
        [self - i for i in other]

    def __len__(self):
        return len(self.personnel)

    def __repr__(self):
        return f"Rota {self.rota}"

    def __str__(self):
        return f"ROTA       : {self.rota}\n" \
               f"PERSONNEL  : {len(self)}\n" \
               f"APPLIANCES : {self.active} appliances on-run"

    def addRole(self, person, constraint=None, rule=None):
        if type(person) is Personnel and person.id[:8] in self._personnelID:
            person.constraint(constraint, rule)
        elif type(person) is str and person in self._personnelID:
            person = self._personnelID[person]
            person.constraint(constraint, rule)
        else:
            print(f"{person} does not exist")

    def activate(self, vehicle, active=True):
        if type(vehicle) is Vehicle:
            self.add(vehicle)
            vehicle.active = active
        elif type(vehicle) is str:
            if vehicle in self._callsigns:
                vehicle = self._callsigns[vehicle]
                vehicle.active = active
            else:
                print(f"{vehicle} is not a <vehicle>")
        else:
            print(f"{vehicle} is not a <vehicle>")

    def deactivate(self, vehicle):
        self.activate(vehicle, False)

    def offRunStation(self):
        [self.deactivate(i) for i in self._callsigns]

    def _save(self, fileName=None, rootDir=None):
        if fileName:
            self._fileName = fileName
        file = os.path.splitext(self._fileName)[0] + ".data"
        if rootDir:
            self._rootDir = rootDir
        with open(os.path.abspath(os.path.expanduser(os.path.join(self._rootDir, file))), 'wb') as f:
            pickle.dump(self(), f, protocol=pickle.HIGHEST_PROTOCOL)

    def _load(self):
        file = os.path.splitext(os.path.join(self._rootDir, self._fileName))[0] + ".data"
        if not os.path.exists(os.path.abspath(os.path.expanduser(file))):
            print("File does not exist. Creating new rota.")
            self._save()  # Creates data file
        else:
            with open(os.path.abspath(os.path.expanduser(file)), 'rb') as f:
                data = pickle.load(f)
            self.rota = data['rota']
            self._personnel = data['personnel']
            self._appliances = data['appliances']
