# -*- coding: utf-8 -*-
"""
Created on Fri Sep 18 23:38:27 2020

Script to manage turnouts every shift

@author: Arif Er
"""

import pickle
import os
import sys


class Rota:
    def __init__(self, rota, fileName=None, rootDir="."):
        if not any([rota, fileName]):
            sys.exit('Provide rota number to create a new rota or log file directory to load data')
        else:
            self.rota, self._fileName, self._rootDir = rota, fileName, rootDir
            self._personnel, self._appliances = [], []
            if self._fileName:
                self._load()
            else:
                self._fileName = f"Rota {self.rota}.data"
                self._rootDir = rootDir

    @property
    def personnel(self):
        return self._personnel

    @property
    def _personnelName(self):
        return [i.name for i in self._personnel]

    @property
    def appliances(self):
        return self._appliances

    @property
    def _applianceName(self):
        return [i.name for i in self._appliances]

    def __add__(self, other):
        if self.rota != other.rota:
            raise TypeError("Only same rotas can be joined together")
        else:
            self.personnel += [i for i in other.personnel if i.name not in self.personnel]
            self.appliances = self.appliances | other.appliances

    def __sub__(self, other):
        if self.rota != other.rota:
            print("ERROR: You can only add the same rota together")
        else:
            self.personnel = [i for i in self.personnel
                              if i not in other.personnel]
            self.appliances = [i for i in self.appliances
                               if i not in other.appliances]

    def __len__(self):
        return len(self.personnel)

    def __repr__(self):
        return f"Rota {self.rota}"

    def __str__(self):
        return f"ROTA {self.rota}\n" \
               f"PERSONNEL: {len(self)}\n" \
               f"APPLIANCES: {self._checkActive()[0]} on-run; {self._checkActive()[1]} off-run"

    def addPersonnel(self, person):
        if type(person) == list:
            if not all([type(i) == Personnel for i in person]):
                print("ERROR: Some personnel in list do not exist. Create entry using Personnel()")
            else:
                [self.personnel.append(i) for i in person if i not in self.personnel]
        elif type(person) != Personnel:
            print(f"ERROR: {person} does not exist. Create an entry for {person} using Personnel()")
        elif person not in self.personnel:
            self.personnel.append(person)
        else:
            pass

    def removePersonnel(self, person):
        if type(person) == list:
            if not all([type(i) == Personnel for i in person]):
                print("ERROR: Some personnel in list do no exist. Remove them from list to continue?\n")
                print(f"REMOVE -> {', '.join([i for i in person if type(i) != Personnel])}")
            else:
                [self.personnel.remove(i) for i in person if i in person]
        elif type(person) != Personnel:
            print(f"ERROR: {person} does not exist.")
        elif person in self.personnel:
            self.personnel.remove(person)
        else:
            pass

    def addRole(self, person, role):
        if person not in self.personnel:
            print(f"ERROR: {person} does not exist. Create an entry for {person} with Personnel()")
        else:
            person.addRole(role)

    def addAppliance(self, appliance):
        if type(appliance) == list:
            if not all([type(i) == Appliance for i in appliance]):
                print(f"ERROR: Some appliance(s) in list do not exist. Create using Appliance()")
            else:
                [self.appliances.append(i) for i in appliance if i not in self.appliances]
        elif type(appliance) != Appliance:
            print(f"ERROR: {appliance} does not exist. Create {appliance} using Appliance()")
        elif appliance not in self.appliances:
            self.appliances.append(appliance)
        else:
            pass

    def removeAppliance(self, appliance):
        if type(appliance) == list:
            if not all([type(i) == Appliance for i in appliance]):
                print("ERROR: Some appliance(s) in list do not exist. Remove them to continue?\n")
                print(f"REMOVE -> {', '.join([i for i in appliance if type(i) != Appliance])}")
            else:
                [self.personnel.remove(i) for i in appliance if i in self.personnel]
        elif type(appliance) != Personnel:
            print(f"ERROR: {appliance} does not exist.")
        elif appliance in self.appliances:
            self.appliances.remove(appliance)
        else:
            pass

    def setPriority(self, appliance, priority):
        if appliance not in self.appliances:
            print(f"ERROR: {appliance} does not exist. Create {appliance} using Appliance()")
        else:
            appliance.setPriority(priority)

    def setRule(self, target, rule):
        if target not in (self.appliances, self.personnel):
            print(f"ERROR: {target} does not exist.")
        else:
            target.setRule(rule)

    def _save(self, fileName=None, rootDir=None):
        if fileName:
            self.fileName = os.path.splitext(fileName)[0] + ".data"
        if rootDir:
            self.rootDir = rootDir
        data = {'rota': self.rota, 'personnel': self.personnel, 'appliances': self.appliances}
        with open(os.path.abspath(os.path.expanduser(os.path.join(self.rootDir, self.fileName))), 'wb') as f:
            pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)

    def _load(self):
        file = os.path.splitext(os.path.join(self.rootDir, self.fileName))[0] + ".data"
        if not os.path.exists(os.path.abspath(os.path.expanduser(file))):
            print("File does not exist. Creating new rota.")
        else:
            with open(os.path.abspath(os.path.expanduser(file)), 'rb') as f:
                data = pickle.load(f)
            self.rota = data['rota']
            self.personnel = data['personnel']
            self.appliances = data['appliances']

    def print(self):
        return print(self)

    def _checkActive(self):
        return len([i for i in self.appliances if i.active]), len([i for i in self.appliances if not i.active])


class Role(object):
    def __init__(self, name, constraint=None, rule=False, inherit=None):
        self.role = name

        if type(rule) is not bool:
            raise TypeError("Only boolean rules are allowed")

        if constraint:
            if type(constraint) is dict:
                for i, j in constraint:
                    if type(j) is not bool:
                        raise TypeError("Only boolean rules are allowed")
                    self._constraints = constraint
            elif type(constraint) is list:
                self._constraints = {i: rule for i in constraint}
            else:
                self._constraints = {constraint: rule}
        else:
            self._constraints = {}

        if inherit:
            inherit = inherit if type(inherit) is list else [inherit]
            [self + i for i in inherit]

    @property
    def constraints(self):
        if type(self._constraints) is dict:
            return self._constraints

    def constraint(self, constraint=None, rule=False):
        if constraint:
            self._constraints.update({constraint: rule})

    def __add__(self, other):
        if type(other) is not Role:
            raise TypeError("Only Roles can be added to Roles")
        else:
            for constraint, rule in other.constraints.items():
                if constraint not in self.constraints:
                    self.constraint(constraint, rule)

    def __repr__(self):
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

    def __repr__(self):
        return f"{self.name} @ {self.role}"


class Appliance(object):
    def __init__(self, name, crew, minimum=1, maximum=1):
        if not crew:
            raise ValueError(f"Assign minimum crew of {name}")
        elif type(crew) is not dict:
            raise TypeError("Crew has to be represented as a dictionary")
        if minimum < maximum:
            raise ValueError(f"Minimum cannot be less than the maximum")
        maximum = maximum if maximum >= sum(crew.values()) else sum(crew.values())

        self._appliance, self._crew, self.limits  = name, crew, [minimum, maximum]

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
    def __init__(self, callsign, appliance, plateNumber, active=True):
        if type(appliance) is not Appliance:
            raise TypeError(f"{appliance} is not an Appliance. Create the object first")
        self._callsign, self._plateNumber, self.active = callsign, plateNumber, active
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

    @plate.setter
    def plate(self, newPlate):
        self._plateNumber = newPlate

    def OnRun(self):
        self.active = True

    def OffRun(self):
        self.active = False

    def __repr__(self):
        return f"{self.callsign} ({self.plate}) -- {'On run' if self.active else 'Off run'}"
