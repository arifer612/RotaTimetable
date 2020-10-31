# -*- coding: utf-8 -*-
"""
Created on Fri Sep 18 23:38:27 2020

Package to manage turnouts every shift

@author: Arif Er
"""

import pickle
import os
import sys
import hashlib
from typing import Union, List, Dict, Tuple, Type, Callable, Any


class Role(object):
    """
    Creates an object that defines the Role of a Personnel.

    Attributes:
        role (str):         Name of the Role.
        constraints (dict): Dictionary of Vehicles and rules. Shows which vehicle the
                            current Role has access to. The constraints are retrieved
                            from 2 sources -- itself and its inherited role. The
                            inherited constraints do not take precedence over its
                            declared constraints.
    """

    def __init__(self, name: str,
                 constraint: Union["Vehicle", dict, list] = None, rule: bool = False,
                 inherit: "Role" = None):

        """
        Args:
            name (str):                       Name of the Role
            constraint (Vehicle, dict, list): Constraints of this Role.

                (Vehicle): Adds the Vehicle to this Role's constraints.

                (dict):    Adds the whole dictionary of constraints as this Role's constraints.

                (list):    Adds the list of Vehicles to this Role's constraints.

            rule (bool):                      Rule for the constraint(s) if constraint is a list or Vehicle.
            inherit (Role):                   Inherits the constraints of this Role.

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

    def constraint(self, constraint: Union["Vehicle", dict, list], rule: bool = False) -> None:
        """
        Declares a new constraint for this Role.

        Args:
           constraint (dict, list, Vehicle): Constraints of this Role.

               (dict):    Adds the whole dictionary of constraints as this Role's constraints.

               (list):    Adds the list of Vehicles to this Role's constraints.

               (Vehicle): Adds the Vehicle to this Role's constraints.

           rule (bool):                      Rule for the constraint(s) if constraint is a list or Vehicle.

        Raises:
            TypeError: If constraints or rules are of the incorrect types.
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
        elif isinstance(constraint, Vehicle):
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

    def __add__(self, other: "Role") -> None:
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
        name (str):         Name of the Personnel.
        id (str):           8-digits unique hash of the Personnel.
        role (str):         Name of the Personnel's Role.
        constraints (dict): Dictionary of Vehicles and rules. Shows which vehicle the
                            current Role has access to. The constraints are retrieved
                            from 2 sources -- itself and its inherited role. The
                            inherited constraints do not take precedence over its
                            declared constraints.
    """

    def __init__(self, name: str, role: Role):
        """
        Args:
            name (str):  Name of the Personnel.
            role (Role): Inherits the properties and attributes of the Role.
        """
        self._name = name
        if not isinstance(role, Role):
            raise TypeError("Only <Role> can be used to create personnel")
        super().__init__(role.role, inherit=role)

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, newName) -> None:
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
        crew (dict):     Dictionary of Roles and their maximum number in the Appliance.
        limits (list):   Minimum and maximum number of Personnel in the Appliance.
    """

    def __init__(self, name, crew: Dict[Role, int], minimum: int = 1, maximum: int = 1):
        """
        Args:
            name (str):    Name of the Appliance.
            crew (dict):   Crew allowed on the Appliance.
            minimum (int): Minimum number of Personnel required on the Appliance.
            maximum (int): Maximum number of Personnel allowed on the Appliance.

        Raises:
            TypeError:  Arguments are of the incorrect types.
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
    def limits(self) -> List[int]:
        return self._limits

    @limits.setter
    def limits(self, newLimits) -> None:
        """
        Changes the crew limits on the Appliance.
        """
        if not isinstance(newLimits, (list, tuple)):
            raise TypeError(f"Limits have to be have to be represented as a list or tuple")
        if len(newLimits) != 2:
            raise ValueError("Incorrect number of limits")
        self._limits = list(newLimits)

    @property
    def appliance(self) -> str:
        return self._appliance

    @appliance.setter
    def appliance(self, newName) -> None:
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

    def change(self, role: Union[Role, dict], value: int = None, minimum: int = None, maximum: int = None) -> None:
        """
        Changes the crew information of the Appliance.

        Args:
            role (Role, dict): Roles to change.

                (Role): Changes the number of 'Role' in the Appliance's crew to 'value'.

                (dict): Updates the crew with the items of the dictionary.

            value (int):       Updates 'role' in crew to 'value'.
            minimum (int):     Updates minimum number of crew required on the Appliance.
            maximum (int):     Updates maximum number of crew allowed on the Appliance.

        Raises:
            TypeError:  Arguments are of the incorrect types.
            ValueError: New crew exceeds maximum number of Personnel allowed in the Appliance.
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
    """
    Creates a Vehicle using an existing Appliance.

    Attributes:
        callsign (str): Unique callsign of the Vehicle.
        plate (str):    Unique plate number of the Vehicle.
        active (bool):  Returns True if the Vehicle is on run and False if the Vehicle is off run.
    """

    def __init__(self, callsign: str, appliance: Appliance, plateNumber: str, active: bool = True):
        """
        Args:
            callsign (str):        Unique callsign of the Vehicle.
            appliance (Appliance): Appliance of the Vehicle.
            plateNumber (str):     Unique plate number of the Vehicle.
            active (bool):         Run state of the Vehicle.

        Raises:
            TypeError: If arguments are of the incorrect types.
        """
        if not isinstance(appliance, Appliance):
            raise TypeError(f"{appliance} is not an Appliance. Create the Appliance first")
        self._callsign, self._plateNumber, self._active = callsign, plateNumber, active
        super().__init__(appliance.appliance, appliance.crew, *appliance.limits)

    @property
    def callsign(self) -> str:
        return self._callsign

    @callsign.setter
    def callsign(self, newCallsign) -> None:
        """
        Changes the callsign of the Vehicle.
        """
        self._callsign = newCallsign

    @property
    def plate(self) -> str:
        return self._plateNumber

    @plate.setter
    def plate(self, newPlate) -> None:
        """
        Changes the plate number of the Vehicle.
        """
        self._plateNumber = newPlate

    @property
    def active(self) -> bool:
        return self._active

    @active.setter
    def active(self, val: bool) -> None:
        """
        Changes the active state of the Vehicle.
        """
        if not isinstance(val, bool):
            raise TypeError("Only <boolean> values are allowed")
        self._active = val

    def onRun(self) -> None:
        """
        Sets active state of the Vehicle to True.
        """
        self.active = True

    def offRun(self) -> None:
        """
        Sets active state of the Vehicle to False.
        """
        self.active = False

    def __repr__(self):
        return f"{self.callsign} ({self.plate}) -- {'On run' if self.active else 'Off run'}"

    def __call__(self) -> Dict[str, Union[str, Dict[Role, int], List[int]]]:
        """
        Returns human-readable data.
        """
        return {
            'callsign': self.callsign,
            'appliance': self.appliance,
            'crew': self.crew,
            'limits': self.limits
        }


def safeLoad(function: Callable) -> Any:
    """
    Decorator to safely edit the Rota.
    """

    def runFunction(self, *args, **kwargs):
        self._load()
        function(self, *args, **kwargs)
        self._save()

    return runFunction


class Rota(object):
    """
    A data structure holding information of the Personnel assigned to the Rota and the turnout history.

    Attributes:
        personnel (List[Personnel]): A list of all the Personnel assigned to the Rota.
    """

    def __init__(self, rota: Union[str, int] = None, fileName: str = None, rootDir: str = "."):
        """
        Args:
            fileName (str):  Name of the save file. If not specified, the default file name will be set to
                             "Rota `rota`".
            rootDir (dir):   Directory where the sve file is located. If not specified, the directory will be set to be
                             the current working directory.
            rota (str, int): The Rota number or name.

        The file will be saved with the *.rt extension.
        """
        if not (rota or fileName):
            sys.exit('Provide rota number to create a new rota or log file directory to load data')
        self.rota, self._fileName, self._rootDir = rota, fileName, rootDir
        self._personnel = {}
        if not self._fileName:
            if not rota:
                raise NameError("Declare rota number to create a new rota")
            self._fileName = f"Rota {self.rota}.rt"
            self._rootDir = rootDir
        self._load()

    @property
    def personnel(self) -> Dict[str, Personnel]:
        return {i.id: i for i in self._personnel}

    def __call__(self, arg=None) -> Union[Personnel, Dict[str, Union[str, List[Personnel]]]]:
        """
        Retrieves specific data from the data structure.

        Args:
            arg (str, Personnel): Retrieves the Personnel from the Rota through the ID or returns the argument if the
                                  Personnel exists in the Rota. Without an argument, returns a human-readable data.
        """
        if arg:
            if isinstance(arg, Personnel) and arg.id in self.personnel:
                return arg
            elif isinstance(arg, str) and arg in self.personnel:
                return self.personnel[arg]
            else:
                print(f"{arg} does not exist in this rota")
        else:
            return {
                'rota': self.rota,
                'personnel': list(self.personnel.values())
            }

    @safeLoad
    def __add__(self, other: Union["Rota", Personnel, List[Union["Rota", Personnel]]]) \
            -> Union[Personnel, List[Personnel]]:
        if isinstance(other, Rota):
            self._personnel = {**self._personnel, **other._personnel}
            return list(other._personnel.values())
        elif isinstance(other, Personnel):
            if other.id not in self.personnel:
                self._personnel.update({other.id: other})
                return other
        elif isinstance(other, list):
            err, new = [], []
            for i in other:
                try:
                    new.append(self + i)
                except TypeError:
                    if type(i) not in err:
                        err.append(type(i))
            if err:
                print(f"{', '.join(err)} cannot be operated on <Rota>")
            return new
        else:
            raise TypeError(f"{type(other)} cannot be operated on <Rota>")

    @safeLoad
    def __sub__(self, other: Union["Rota", Personnel, List[Union["Rota", Personnel]]]) -> Union[str, List[str]]:
        if isinstance(other, Rota):
            self._personnel = list(set(self.personnel) - set(other.personnel))
            return list(other.personnel)
        elif isinstance(other, Personnel):
            if other.id in self.personnel:
                self._personnel.pop(list(self.personnel).index(other.id))
                return other.id
        elif isinstance(other, list):
            err, rem = [], []
            for i in other:
                try:
                    rem(self - i)
                except TypeError:
                    if type(i) not in err:
                        err.append(type(i))
            if err:
                print(f"{', '.join(err)} cannot be operated on <Rota>")
            return rem
        else:
            raise TypeError(f"{type(other)} cannot be operated on <Rota>")

    def add(self, other: Union["Rota", Personnel, str, List[Union["Rota", Personnel, str]]], *args, **kwargs)\
            -> Union[Personnel, List[Personnel]]:
        """
        Adds or creates Personnel to the Rota.

        Args:
            other (list, Personnel, Rota): A list of Personnel, a Personnel, or a Rota to add to the Rota.
            args:                          Optional arguments required to create a new personnel.
            kwargs:                        Optional keyword arguments required to create a new personnel.

        Returns:
            The Personnel added to the Rota.

        Raises:
            TypeError: If the item(s) being added to the Rota is/are not Personnel or Rota.
        """
        if isinstance(other, (Personnel, Rota)):
            return self + other
        elif isinstance(other, str):
            newPersonnel = Personnel(other, *args, **kwargs)
            return self + newPersonnel
        elif isinstance(other, list):
            newPersonnel = [self.add(i) for i in other]
            return newPersonnel
        else:
            raise TypeError(f"{type(other)} cannot be operated on <Rota>")

    def sub(self, other: Union["Rota", Personnel, List[Union["Rota", Personnel]]]):
        """
        Removes Personnel from the Rota.

        Args:
            other (list, Personnel): A list of Personnel, a Personnel, or a subset of a Rota to remove from the Rota.

        Raise:
            TypeError: If the item(s) being added to the Rota is/are not Personnel or Rota.
        """
        self - other

    def __len__(self) -> int:
        return len(self.personnel)

    def __repr__(self):
        return f"Rota {self.rota}"

    def __str__(self):
        return f"ROTA       : {self.rota}\n" \
               f"PERSONNEL  : {len(self)}\n"

    def addRole(self, person: Union[Personnel, str], constraint: Union[Dict[Vehicle, bool], Vehicle] = None,
                rule: bool = None) -> None:
        """"""
        if isinstance(person, Personnel) and person.id in self.personnel:
            person.constraint(constraint, rule)
        elif isinstance(person, str) and person in self.personnel:
            person = self.personnel[person]
            person.constraint(constraint, rule)
        else:
            print(f"{person} does not exist")

    def _save(self, fileName: str = None, rootDir: str = None) -> None:
        if fileName:
            self._fileName = fileName
        file = os.path.splitext(self._fileName)[0] + ".rt"
        if rootDir:
            self._rootDir = rootDir
        with open(os.path.abspath(os.path.expanduser(os.path.join(self._rootDir, file))), 'wb') as f:
            pickle.dump(self(), f, protocol=pickle.HIGHEST_PROTOCOL)

    def _load(self) -> None:
        file = os.path.splitext(os.path.join(self._rootDir, self._fileName))[0] + ".rt"
        if not os.path.exists(os.path.abspath(os.path.expanduser(file))):
            print("File does not exist. Creating new rota.")
            self._save()  # Creates data file
        else:
            with open(os.path.abspath(os.path.expanduser(file)), 'rb') as f:
                data = pickle.load(f)
            self.rota, self._personnel = data['rota'], data['personnel']


class Station(object):
    """
    Creates a Station. The assets of the Station are Roles, Appliances, Vehicles, and Rotas. The data structure of the
    Station is a dictionary of the assets and their unique IDs as keys.

    Attributes:
        roles (dict[str: Role]):           Dictionary of the Roles present in the Station.
        appliances (dict[str: Appliance]): Dictionary of the Appliances present in the Station.
        vehicles (dict[str: Vehicle]):     Dictionary of the Vehicles present in the Station.
        rotas (dict[str: Rota]):           Dictionary of the Rotas present in the Station.
        active (list):                     List of all the Vehicles that are on run in the Station.
        data (dict):                       Dictionary of all the assets in the Station.
    """
    _assets = Union[Role, Appliance, Vehicle, Rota]

    def __init__(self, name: str, fileName: str = None, rootDir: str = '.'):
        """
        Args:
            name (str):     Name of the Station.
            fileName (str): Name of the save file. If not specified, the file name will be the same as `name`.
            rootDir (dir):  Directory where the sve file is located. If not specified, the directory will be set to be
                            the current working directory.

        The file will be saved with the *.stn extension.
        """
        self.name, self._fileName, self._rootDir = name, fileName, rootDir
        self._roles = self._appliances = self._vehicles = self._rotas = {}
        if not self._fileName:
            self._fileName = self.name
        self._load()

    @property
    def roles(self) -> Dict[str, Role]:
        return self._roles

    @property
    def appliances(self) -> Dict[str, Appliance]:
        return self._appliances

    @property
    def vehicles(self) -> Dict[str, Vehicle]:
        return self._vehicles

    @property
    def rotas(self) -> Dict[Union[str, int], Rota]:
        return self._rotas

    @property
    def active(self) -> List[Vehicle]:
        return [i for i in self.vehicles.values() if i.active]

    @property
    def data(self) -> Dict[Union[str, int], Union[str, Role, Appliance, Vehicle, Rota]]:
        """
        Returns human-readable data.
        :return:
        """
        return {**self.roles, **self.appliances, **self.vehicles, **self.rotas}

    def __call__(self, arg: Union[str, int, _assets]) -> Union[_assets, dict]:
        """
        Returns:
             The Station asset or the dictionary of assets.

        Raises:
            KeyError: If asset identifier or asset does not exist in the Station.
        """
        if arg:
            return self.data[arg]
        else:
            return self.data

    def _addAsset(self, arg1: Union[_assets, str, int, List[_assets]], Asset: Type[_assets],
                  assetIdentifier: str, assetDict: str = None, **kwargs) \
            -> Union[_assets, List[_assets]]:
        """
        General Asset generation method. The Assets can be any from Role, Appliance, Vehicle, or Rota.

        Args:
            arg1 (Asset, str, list): The Asset to add.

                (Asset): Adds an existing Asset to the Station.

                (str):   Name/Callsign/Rota of the Asset.

                (list):  List of Assets to add to the Station.

            Asset (class):           Asset to generate.
                        # Role, Appliance, Vehicle, Rota
            assetIdentifier (str):   Unique identifier of the Asset.
            assetDict (str):         Unique dictionary identifier of the Asset.
            kwargs:                  Remaining arguments required to create the Asset.

        Returns:
            Asset

        Raises:
            TypeError: If kwargs are of the incorrect types
        """
        if assetDict:
            if not isinstance(assetDict, str) or assetDict not in self.__dir__():
                raise AttributeError(f"{str(assetDict)} is not an attribute of Station.")
            _assetDict, assetDict = assetDict, self.__getattribute__(assetDict)
        else:
            _assetDict, assetDict = f"_{assetIdentifier}s", self.__getattribute__(f"_{assetIdentifier}s")

        if isinstance(arg1, Asset) and arg1.__getattribute__(assetIdentifier) in assetDict:

            return assetDict[arg1.__getattribute__(assetIdentifier)]
        elif isinstance(arg1, str) and arg1 in assetDict:
            return assetDict[arg1]
        elif isinstance(arg1, list):
            data = []
            data.extend(Asset for i in arg1 if isinstance(i, Asset))
            if len(data) < len(arg1):
                print(f"{', '.join([str(i) for i in arg1 if arg1 is not isinstance(i, Asset)])}")
            return data
        else:  # Tries to create the asset using the arguments
            asset = Asset(arg1, **kwargs)
            self._load()
            identifier = asset.__getattribute__(assetIdentifier)

            if identifier in self.data and identifier not in assetDict:
                raise TypeError(f"{arg1} has already been declared as a <{self.data[identifier]}>")

            if identifier not in assetDict:
                self.__getattribute__(_assetDict).update({identifier: asset})
                self._save()
                return asset
            else:
                return assetDict[identifier]

    def role(self, name: Union[Role, str, List[Role]],
             constraint: Union[Vehicle, dict, List[Vehicle]] = None, rule: bool = False, inherit: Role = None) \
            -> Union[Role, List[Role]]:
        """
        Creates and adds a Role as a Station asset.

        Args:
            name (str, Role, list):           The Role to add to the Station.

                (Role):     Adds an existing Role to the Station.

                (str):      Name of the Role to be created.

                (list):     List of Roles to add to the Station.

            constraint (dict, list, Vehicle): Constraints of this Role.

                (dict):     Adds the whole dictionary of constraints as this Role's constraints.

                (list):     Adds the list of Vehicles to this Role's constraints.

                (Vehicle):  Adds the Vehicle to this Role's constraints.

            rule (bool):                      Rule for the constraint(s) if constraint is a list or Vehicle.
            inherit (Role):                   Inherits the constraints of this Role.

        Returns:
            Role(s) added to the station

        Raises:
            TypeError: If arguments are of the incorrect types.
        """
        return self._addAsset(name, Role, 'role',
                              constraint=constraint, rule=rule, inherit=inherit)

    def appliance(self, name: Union[Role, str, List[Appliance]],
                  crew: Dict[Role, int] = None, minimum: int = 1, maximum: int = 1) \
            -> Union[Appliance, List[Appliance]]:
        """
        Creates and adds an Appliance as a Station asset.

        Args:
            name (Appliance, str, list): The Appliance to add to the Station.

                (Appliance): Adds an existing Appliance to the Station.

                (str):       Name of the Appliance to be created.

                (list):      List of Appliances to be added to the Station.

            crew (dict):                 Crew allowed on the Appliance.
            minimum (int):               Minimum number of Personnel required on the Appliance.
            maximum (int):               Maximum number of Personnel allowed on the Appliance.

        Returns:
            Appliance(s) added to the Station.

        Raises:
            TypeError:  If arguments are of the incorrect types.
            ValueError: Crew not added or maximum is more than minimum.
        """
        return self._addAsset(name, Appliance, 'appliance',
                              crew=crew, minimum=minimum, maximum=maximum)

    def vehicle(self, callsign: Union[Vehicle, str, List[Vehicle]],
                appliance: Appliance = None, plateNumber: str = None, active: bool = True)\
            -> Union[Vehicle, List[Vehicle]]:
        """
        Args:
            callsign (Vehicle, str, list): The Vehicle to add to the Station.

                (Vehicle): Adds an existing Vehicle to the Station.

                (str):     Unique callsign of the Vehicle to be created.

                (list):    List of Vehicles to add to the Station.

            appliance (Appliance):         Appliance of the Vehicle.
            plateNumber (str):             Unique plate number of the Vehicle.
            active (bool):                 Run state of the Vehicle.

        Raises:
            TypeError: If arguments are of the incorrect type.
        """
        return self._addAsset(callsign, Vehicle, 'callsign', '_vehicles',
                              appliance=appliance, plateNumber=plateNumber, active=active)

    def rota(self, rota: Union[Rota, int, str, List[Rota]], fileName: str = None, rootDir: str = '.') \
            -> Union[Rota, List[Rota]]:
        """
        Args:
            rota (Rota, int, list): The Rota to add to the Station:

                (Rota):     Adds an existing Rota to the Station.

                (int, str): The number or name of the Rota to be created.

                (list):     List of Rotas to add to the Station.

            fileName (str):         Name of the save file. If not specified, the default file name will be set to
                                    "Rota `rota`".
            rootDir (str):          Directory where the sve file is located. If not specified, the directory will be set
                                    to be the current working directory.

        The file will be saved with the *.rt extension.
        """
        return self._addAsset(rota, Rota, 'rota',
                              fileName=fileName, rootDir=rootDir)

    def personnel(self, rota: Union[Rota, int, List[Union[Rota, int]]],
                  name: Union[Personnel, str, List[Union[Personnel, str]]], role: Role = None) \
            -> Union[Personnel, List[Personnel]]:
        """
        Creates and adds Personnel to a specific Rota.

        Args:
            rota (Rota, int, list):      Rota(s) to add Personnel to.
            name (Personnel, str, list): (List of) Personnel to create and add to the specified Rota.

                (Personnel): Adds existing Personnel to the Rota(s).

                (str):       Name of the Personnel to be created.

                (list):      List of Personnel to add to the Rota(s)

            role (Role):                 Role of Personnel to create.

        Returns:
            Personnel that has been added to the Rota
        """
        if not isinstance(rota, (Rota, int, list)):
            raise TypeError("<Personnel> can be added only to a <Rota>")
        elif isinstance(rota, Rota):
            if rota.rota not in self.rotas:
                raise KeyError(f"Rota {rota.rota} is not in the Station")
            rota = [self(rota.rota)]
        elif isinstance(rota, int):
            if rota in self.rotas:
                raise KeyError(f"Rota {rota} is not in the Station")
            rota = [self(rota)]
        elif isinstance(rota, list):
            if not (all(isinstance(i, Rota) for i in rota) or all(isinstance(i, int) for i in rota)):
                raise TypeError(f"{', '.join([i for i in rota if not isinstance(i, Rota)])} is/are not <Rota>")
            if all(isinstance(i, int) for i in rota):
                rota = [self(i) for i in rota]
            pass
        else:
            raise TypeError("<Personnel> can be added only to a <Rota>")

        result = errs = []
        for r in rota:
            try:
                if isinstance(name, Personnel):
                    r + name
                    result.append(name)
                elif isinstance(name, str):
                    if not (role or isinstance(role, Role)):
                        raise TypeError
                    p = Personnel(name, role)
                    r + p
                    result.append(p)
                elif isinstance(name, list):
                    [self.personnel(r, i, role) for i in name]
                else:
                    raise NameError(f"{str(name)}")
            except NameError as err:
                errs.append(err.args[0])
            except TypeError:
                raise TypeError("A <Role> has to be specified")

        if errs:
            print(f"{', '.join([str(i) for i in errs])} has/have to be <Personnel> to be added to <Rota>.")

        return result if len(result) > 0 else result[0]

    def __add__(self, other: Union[_assets, List[_assets]]) -> Union[_assets, List[_assets]]:
        if isinstance(other, Rota):
            return self.rota(other)
        elif isinstance(other, Role):
            return self.role(other)
        elif isinstance(other, Appliance):
            return self.appliance(other)
        elif isinstance(other, Vehicle):
            return self.vehicle(other)
        elif isinstance(other, list):
            return [self + i for i in other]
        else:
            raise TypeError(f"{type(other)} cannot be operated on <Station>")

    def __sub__(self, other: Union[str, _assets, List[Union[str, _assets]]]) -> None:
        if isinstance(other, Rota):
            self._rotas.pop(other.rota, None)
        elif isinstance(other, Role):
            self._roles.pop(other.role, None)
        elif isinstance(other, Appliance):
            self._appliances.pop(other.appliance, None)
        elif isinstance(other, Vehicle):
            self._vehicles.pop(other.callsign, None)
        elif isinstance(other, str):
            if other not in self.data:
                raise KeyError(f"{other} is not a Station asset")
            other = self.data[other]
            self - other
        elif isinstance(other, list):
            errk = errt = errs = []
            for i in other:
                try:
                    self - i
                except KeyError as err:
                    errk.append(err.args[0].split(' is not a ')[0])
                except TypeError as err:
                    errt.append(err.args[0].split(' has to be')[0])
            if errk:
                errs.append(f"{', '.join([i for i in errk])} is/are not Station asset(s).")
            if errt:
                errs.append(f"{', '.join([i for i in errt])} has/have to be <Role>, <Appliance>, <Vehicle>, or <Rota>.")
            if errs:
                raise TypeError(' '.join(errs))
        else:
            raise TypeError(f"{other} has to be a <Role>, <Appliance>, <Vehicle>, or <Rota>")

    def add(self, other: Union[_assets, List[_assets]]) -> Union[_assets, List[_assets]]:
        """
        Adds an asset or a list of assets to the Station.

        Args:
            other (Role, Appliance, Vehicle, Rota, list): The asset or list of assets to add to the Station.

        Return:
            The asset added to the Station.
        """
        return self + other

    def remove(self, other: Union[str, _assets, List[Union[str, _assets]]]) -> None:
        """
        Removes an asset or a list of assets from the Station.

        Args:
            other (Role, Appliance, Vehicle, Rota, list): The asset or list of assets to remove from the Station.
        """
        self - other

    def activate(self, vehicle: Union[Vehicle, str, List[Union[Vehicle, str]]], active: bool = True) -> None:
        """
        Changes the active status of a Vehicle asset from the Station.

        Args:
            vehicle (Vehicle, str, list): Changes the active status the Vehicle(s).
            active (bool):                Active -> True; Not active -> False.
        """
        if isinstance(vehicle, Vehicle):
            self.add(vehicle)
            vehicle.active = active
        elif isinstance(vehicle, str):
            if vehicle in self.vehicles:
                self.vehicles[vehicle].active = active
            else:
                raise NameError(f"{vehicle} is not a <Vehicle>")
        elif isinstance(vehicle, list):
            for v in vehicle:
                self.activate(v, active)
        else:
            raise NameError(f"{vehicle} is not a <Vehicle>")

    def deactivate(self, vehicle: Union[Vehicle, str, List[Union[Vehicle, str]]]) -> None:
        """
        Changes the active status of a Vehicle asset from the Station to False.

        Args:
            vehicle (Vehicle, str, list): Changes the active status the Vehicle(s) to False.
        """
        self.activate(vehicle, False)

    def offRun(self) -> None:
        """
        Changes the active status of all the Vehicle assets from the Station to False.
        """
        [self.deactivate(i) for i in self.vehicles]

    def _save(self, fileName: str = None, rootDir: str = None) -> None:
        """
        Saves Station data on disk.

        Args:
            fileName (str): Name of the save file. If not specified, the default file name will be used.
            rootDir (dir):  Directory where the sve file is located. If not specified, the default directory will
                            be used.
        """
        if fileName:
            self._fileName = fileName
        file = os.path.splitext(self._fileName)[0] + ".stn"
        if rootDir:
            self._rootDir = rootDir
        with open(os.path.abspath(os.path.expanduser(os.path.join(self._rootDir, file))), 'wb') as f:
            data = (self.roles, self.appliances, self.vehicles, self.rotas)
            pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)

    def _load(self) -> None:
        """
        Loads Station data from disk if it exists or creates a new one if it does not.
        """
        file = os.path.splitext(os.path.join(self._rootDir, self._fileName))[0] + ".stn"
        if not os.path.exists(os.path.abspath(os.path.expanduser(file))):
            print("File does not exist. Creating new station.")
            self._save()  # Creates data file
        else:
            with open(os.path.abspath(os.path.expanduser(file)), 'rb') as f:
                data = pickle.load(f)
            self._roles, self._appliances, self._vehicles, self._rotas = data


def loadGlobal(data: dict):
    for i in data:
        globals()[i] = data[i]
