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
from typing import Union, Dict, Tuple, NewType


class Role(object):
    """
    Creates an object that defines the Role of a Personnel.

    Attributes:
        role (str): Name of the Role.
        constraints (dict): Dictionary of Vehicles and rules. Shows which vehicle the
                            current Role has access to. The constraints are retrieved
                            from 2 sources -- itself and its inherited role. The
                            inherited constraints do not take precedence over its
                            declared constraints.
    """
    def __init__(self, name,
                 constraint: Union["Vehicle", dict, list] = None, rule: bool = False,
                 inherit: "Role" = None):

        """
        Args:
            :param name (str): Name of the Role
            constraint (dict, list, Vehicle): Constraints of this Role.

                (dict): Adds the whole dictionary of constraints as this Role's constraints.

                (list): Adds the list of Vehicles to this Role's constraints.

                (Vehicle): Adds the Vehicle to this Role's constraints.
            rule (bool): Rule for the constraint(s) if constraint is a list or Vehicle.
            inherit (Role): Inherits the constraints of this Role.

        Raises:
            TypeError: If arguments are of the incorrect type.
        """
        self.role, self._constraints, self._inheritance = name, {}, inherit

        if not isinstance(rule, bool):
            raise TypeError("Only boolean rules are allowed")

        if inherit:
            if not isinstance(inherit, Role):
                raise TypeError("Only <Role> can be inherited")

        if constraint:
            self.constraint(constraint)

    @property
    def constraints(self) -> Dict["Vehicle", bool]:
        """
        Updates the Role's constraints if the inherited Role has a new constraint unless
        declared beforehand. The declaration is usually made when creating the instance
        and may be done post-creation through the constraint() method.
        """
        if self._inheritance:
            return {**self._inheritance.constraints, **self._constraints}
        else:
            return self._constraints

    def constraint(self, constraint: Union["Vehicle", dict, list], rule: bool = False):
        """
        Declares a new constraint for this Role.
        Args:
           constraint (dict, list, Vehicle): Constraints of this Role.

               (dict): Adds the whole dictionary of constraints as this Role's constraints.

               (list): Adds the list of Vehicles to this Role's constraints.

               (Vehicle): Adds the Vehicle to this Role's constraints.
           rule (bool): Rule for the constraint(s) if constraint is a list or Vehicle.
        """
        if isinstance(constraint, dict):
            err = erri = errj = []
            for i, j in constraint.items():
                if not isinstance(i, Vehicle):
                    erri.append(i)
                if not isinstance(j, bool):
                    errj.append(j)
                if erri:
                    err.append(f"{', '.join(erri)}: Only <Vehicle> can be added as constraints")
                if errj:
                    err.append(f"{', '.join(errj)}: Only <boolean> rules are allowed")
                if err:
                    raise TypeError(f"{'& '.join(err)}")

            self._constraints.update(constraint)
        elif isinstance(constraint, "Vehicle"):
            if not isinstance(rule, bool):
                raise TypeError("Only <boolean> rules are allowed")
            self._constraints.update({constraint: rule})
        elif isinstance(constraint, list):
            errs = []
            for i in constraint:
                if not isinstance(i, Vehicle):
                    errs.append(i)
            if errs:
                raise TypeError(f"{', '.join(errs)}: Only <Vehicle> can be added as constraints")

            [self._constraints.update({i: rule}) for i in constraint]
        else:
            raise TypeError("Only <Vehicle> can be added as constraints")

    def __add__(self, other: "Role"):
        """
        Defines a one-way operation to add the constraint of an existing Role to the current Role.
        """
        if not isinstance(other, Role):
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

    def __call__(self) -> Tuple[str, Dict["Vehicle", bool], str]:
        """
        Returns human-readable data.
        """
        return self.role, self.constraints, self._inheritance.role


class Personnel(Role):
    """
    Creates a Personnel using an existing Role.

    Attributes:
        name (str): Name of the Personnel.
        id (str): 8-digits unique hash of the Personnel.
        role (str): Name of the Personnel's Role.
        constraints (dict): Dictionary of Vehicles and rules. Shows which vehicle the
                            current Role has access to. The constraints are retrieved
                            from 2 sources -- itself and its inherited role. The
                            inherited constraints do not take preceedence over its
                            declared constraints.
    """
    def __init__(self, name, role: Role):
        """
        Args:
            name (str): Name of the Personnel.
            role (Role): Inherits the properties and attributes of the Role.
        """
        self._name = name
        if not isinstance(role, Role):
            raise TypeError("Only <Role> can be used to create personnel")
        super().__init__(role.role, inherit=role)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, newName):
        """
        Changes the name of the Personnel.
        """
        self._name = newName

    @property
    def __id(self) -> str:
        return hashlib.sha1(f"{self.name} @ {self.role}".encode()).hexdigest()

    @property
    def id(self) -> str:
        """
        8 digits slice of the unique hash of the Personnel.
        """
        return self.__id[10:17]

    def __repr__(self):
        return self.id

    def __str__(self):
        return self.name

    def __call__(self) -> Dict[str, Union[str, Dict["Vehicle", bool]]]:
        """
        Returns human-readable data.
        """
        return {
            'name': self.name,
            'role': self.role,
            'constraints': self.constraints
        }


class Appliance(object):
    """
    Creates an object that defines the Appliance of a Vehicle.

    Attributes:
        appliance (str): Name of the Appliance.
        crew (dict): Dictionary of Roles and their maximum number in the Appliance.
        limits (list): Minimum and maximum number of Personnel in the Appliance.
    """
    def __init__(self, name, crew: dict, minimum: int = 1, maximum: int = 1):
        """
        Args:
            name (str): Name of the Appliance.
            crew (dict): Crew allowed on the Appliance.
            minimum (int): Minimum number of Personnel required on the Appliance.
            maximum (int): Maximum number of Personnel allowed on the Appliance.

        Raises:
            TypeError: Arguments are of the incorrect types.
            ValueError: Crew not added or maximum is more than minimum.
        """
        if not crew:
            raise ValueError(f"Assign minimum crew of {name}")
        elif not isinstance(crew, dict):
            raise TypeError("Crew has to be represented as a <dict>")
        if not (isinstance(minimum, int) and isinstance(maximum, int)):
            raise TypeError("Minimum and Maximum have to be <integer>")
        if maximum < minimum:
            raise ValueError(f"Maximum cannot be less than the minimum")
        maximum = maximum if maximum >= sum(crew.values()) else sum(crew.values())
        self._appliance, self._crew, self._limits = name, crew, [minimum, maximum]

    @property
    def limits(self):
        return self._limits

    @limits.setter
    def limits(self, newLimits):
        """
        Changes the crew limits on the Appliance.
        """
        if not isinstance(newLimits, (list, tuple)):
            raise TypeError(f"Limits have to be have to be represented as a list or tuple")
        if len(newLimits) != 2:
            raise ValueError("Incorrect number of limits")
        self._limits = list(newLimits)

    @property
    def appliance(self):
        return self._appliance

    @appliance.setter
    def appliance(self, newName):
        """
        Changes the name of the Appliance.
        """
        self._appliance = newName

    @property
    def crew(self) -> Dict[Role, int]:
        self._crew = {i: v for (i, v) in self._crew.items() if v}
        return self._crew

    def __repr__(self):
        return f"{self.crew}"

    def __call__(self) -> Tuple[str, Dict[Role, int], int]:
        """
        Returns human-readable data.
        """
        return (self.appliance, self.crew, *self.limits)

    def change(self, role: Union[Role, dict], value: int = None, minimum: int = None, maximum: int = None):
        """
        Changes the crew information of the Appliance.

        Args:
            role (Role, dict): Roles to change

                (Role): Changes the number of 'Role' in the Appliance's crew to 'value'.  

                (dict): Updates the crew with the items of the dictionary.  
            value (int): Updates 'role' in crew to 'value'
            minimum (int): Updates minimum number of crew required on the Appliance.
            maximum (int): Updates maximum number of crew allowed on the Appliance.

        Raises:
            TypeError: Arguments are of the incorrect types.
            Value Error: New crew exceeds maximum number of Personnel allowed in the Appliance.
        """
        if minimum:
            if not isinstance(minimum, int):
                raise TypeError("Minimum has to be an <integer>")
            self.limits[0] = minimum
        if maximum:
            if not isinstance(maximum, int):
                raise TypeError("Maximum has to be an <integer>")
            self.limits[1] = maximum

        if isinstance(role, dict):
            err = erri = errj = []
            for i, j in role.items():
                if not isinstance(i, Role):
                    erri.append(i)
                if not isinstance(j, int):
                    errj.append(j)
            if erri:
                err.append(f"{', '.join(erri): Only <Role> can be added to crew}")
            if errj:
                err.append(f"{', '.join(errj): Only <integer> values are allowed}")
            if err:
                raise TypeError(f"{'& '.join(err)}")
        elif isinstance(role, Role):
            if not value:
                raise AttributeError(f"Number of {role} has to be declared")
            elif not isinstance(value, int):
                raise TypeError("Only <integer> values are allowed")
            role = {role: value}
        else:
            raise TypeError("Only <Role> can be added to crew.")

        crew = {**self.crew, **role}
        if sum(crew.values()) > self.limits[1]:
            raise ValueError("Total crew exceeds maximum of the appliance")
        self._crew.update(role)


class Vehicle(Appliance):
    def __init__(self, callsign, appliance: Appliance, plateNumber, active: bool = True):
        if not isinstance(appliance, Appliance):
            raise TypeError(f"{appliance} is not an Appliance. Create the Appliance first")
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

    @plate.setter
    def plate(self, newPlate):
        self._plateNumber = newPlate

    @property
    def active(self):
        return self._active

    @active.setter
    def active(self, val: bool):
        if not isinstance(val, bool):
            raise TypeError("Only <boolean> values are allowed")
        self._active = val

    def onRun(self):
        self.active = True

    def offRun(self):
        self.active = False

    def __repr__(self):
        return f"{self.callsign} ({self.plate}) -- {'On run' if self.active else 'Off run'}"

    def __call__(self):
        return {
            'callsign': self.callsign,
            'appliance': self.appliance,
            'crew': self.crew,
            'limits': self.limits
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
        self.rota, self._fileName, self._rootDir = rota, fileName, rootDir
        self._personnel = []
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
        return {i.id: i for i in self._personnel}

    def __call__(self, arg=None):
        if arg:
            if isinstance(arg, (Personnel, Vehicle)):
                return arg
            elif isinstance(arg, str):
                if arg in self._personnelID:
                    return self._personnelID[arg]
                else:
                    print(f"{arg} does not exist in this rota")
        else:
            return {
                'rota': self.rota,
                'personnel': [i() for i in self.personnel]
            }

    @safeLoad
    def __add__(self, other):
        if isinstance(other, Rota):
            self._personnel = list(set(self.personnel) | set(other.personnel))
        elif isinstance(other, Personnel):
            if other.id not in self._personnelID:
                self._personnel.append(other)
        else:
            raise TypeError(f"{type(other)} cannot be operated on <Rota>")

    @safeLoad
    def __sub__(self, other):
        if isinstance(other, Rota):
            self._personnel = list(set(self.personnel) - set(other.personnel))
        elif isinstance(other, Personnel):
            if other.id in self._personnelID:
                self._personnel.pop(list(self._personnelID).index(other.id))
        else:
            raise TypeError(f"{type(other)} cannot be operated on <Rota>")

    def add(self, other: Personnel):
        if not isinstance(other, list):
            other = [other]
        [self + i for i in other]

    def sub(self, other: Personnel):
        if not isinstance(other, list):
            other = [other]
        [self - i for i in other]

    def __len__(self):
        return len(self.personnel)

    def __repr__(self):
        return f"Rota {self.rota}"

    def __str__(self):
        return f"ROTA       : {self.rota}\n" \
               f"PERSONNEL  : {len(self)}\n"

    def addRole(self, person, constraint=None, rule=None):
        if isinstance(person, Personnel) and person.id in self._personnelID:
            person.constraint(constraint, rule)
        elif isinstance(person, str) and person in self._personnelID:
            person = self._personnelID[person]
            person.constraint(constraint, rule)
        else:
            print(f"{person} does not exist")

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


class Station(object):
    def __init__(self, name, fileName=None, rootDir='.'):
        self.name, self._fileName, self._rootDir = name, fileName, rootDir
        self._roles = self._appliances = self._vehicles = self._rotas = {}
        if not self._fileName:
            self._fileName = self.name

    @property
    def roles(self):
        return self._roles

    @property
    def appliances(self):
        return self._appliances

    @property
    def vehicles(self):
        return self._vehicles

    @property
    def rotas(self):
        return self._rotas

    @property
    def active(self):
        return [i for i in self.vehicles if i.active]

    @property
    def data(self):
        return {**self.roles, **self.appliances, **self.vehicles, **self.rotas}

    def __call__(self, *args, **kwargs):
        if args:
            return self.data[args[0]]
        else:
            return self.data

    def checkExistence(self, data, dataName, dataDict):
        self._load()
        if dataName in self.data and dataName not in dataDict:
            raise TypeError(f"{dataName} has already been declared as a <{self.data[dataName]}>")

        if dataName not in dataDict:
            dataDict.update({dataName: data})
            self._save()
            return data
        else:
            return dataDict[dataName]

    def role(self, *args, **kwargs) -> Role:
        if args[0] in self.roles:
            return self.roles[args[0]]

        if 'role' in kwargs:
            role = kwargs['role']
        else:
            role = Role(*args, **kwargs)

        return self.checkExistence(role, role.role, self.roles)

    def appliance(self, *args, **kwargs) -> Appliance:
        if args[0] in self.appliances:
            return self.appliances[args[0]]

        if 'appliance' in kwargs:
            app = kwargs['appliance']
        else:
            app = Appliance(*args, **kwargs)

        return self.checkExistence(app, app.appliance, self.appliances)

    def vehicle(self, *args, **kwargs) -> Vehicle:
        if args[0] in self.vehicles:
            return self.vehicles[args[0]]

        if 'vehicle' in kwargs:
            veh = kwargs['vehicle']
        else:
            veh = Vehicle(*args, **kwargs)

        return self.checkExistence(veh, veh.callsign, self.vehicles)

    def rota(self, *args, **kwargs):
        if args[0] in self.rotas:
            return self.rotas[args[0]]

        if 'rota' in kwargs:
            rota = kwargs['rota']
        else:
            rota = Rota(*args, **kwargs)

        return self.checkExistence(rota, rota.rota, self.rotas)

    def personnel(self, rota, name, role: Role) -> Personnel:
        if not isinstance(role, Role):
            if role in self.roles:
                role = self.roles[role]
            else:
                raise TypeError(f"{role} has to be a <Role>")

        person = Personnel(name, role)
        self(rota).add(person)
        return person

    def __add__(self, other):
        if isinstance(other, Rota):
            self.rota(rota=other)
        elif isinstance(other, Role):
            self.role(role=other)
        elif isinstance(other, Appliance):
            self.appliance(appliance=other)
        elif isinstance(other, Vehicle):
            self.vehicle(vehicle=other)
        elif isinstance(other, list):
            [self + i for i in other]
        else:
            raise TypeError(f"{type(other)} cannot be operated on <Station>")

    def add(self, other):
        self + other

    def activate(self, vehicle, active=True):
        if isinstance(vehicle, Vehicle):
            self.add(vehicle)
            vehicle.active = active
        elif isinstance(vehicle, str):
            if vehicle in self.vehicles:
                self.vehicles[vehicle].active = active
            else:
                raise NameError(f"{vehicle} is not a <Vehicle>")
        else:
            raise NameError(f"{vehicle} is not a <Vehicle>")

    def deactivate(self, vehicle):
        self.activate(vehicle, False)

    def offRunStation(self):
        [self.deactivate(i) for i in self.vehicles]

    def _save(self, fileName=None, rootDir=None):
        if fileName:
            self._fileName = fileName
        file = os.path.splitext(self._fileName)[0] + ".stn"
        if rootDir:
            self._rootDir = rootDir
        with open(os.path.abspath(os.path.expanduser(os.path.join(self._rootDir, file))), 'wb') as f:
            data = (self.roles, self.appliances, self.vehicles, self.rotas)
            pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)

    def _load(self):
        file = os.path.splitext(os.path.join(self._rootDir, self._fileName))[0] + ".stn"
        if not os.path.exists(os.path.abspath(os.path.expanduser(file))):
            print("File does not exist. Creating new rota.")
            self._save()  # Creates data file
        else:
            with open(os.path.abspath(os.path.expanduser(file)), 'rb') as f:
                data = pickle.load(f)
            self._roles, self._appliances, self._rotas = data
