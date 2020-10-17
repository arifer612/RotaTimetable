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
    def __init__(self, rota=None, fileName=None, rootDir=None):
        if not any([rota, fileName]):
            sys.exit('Provide rota to create a new rota, or log file to load data')
        else:
            self.rota, self.fileName, self.rootDir = rota, fileName, rootDir
            self.personnel, self.appliances = [], []
            if self.fileName:
                self.load()
        
    def __add__(self, other):
        if self.rota != other.rota:
            raise TypeError
        else:
            self.personnel += other.personnel
            self.appliances += other.appliances
        
    def __sub__(self, other):
        if self.rota != other.rota:
            print("ERROR: You can only add the same rota together")
        else:
            self.personnel = [i for i in self.personnel 
                              if i not in other.personnel]
            self.appliances = [i for i in self.appliances
                               if i not in other.appliances]
        
    def addPersonnel(self, person):
        if type(person) != Personnel:
            print(f"ERROR: {person} does not exist. Create an entry for {person} with Personnel()")
        elif person not in self.personnel:
            self.personnel.append(person)
        else:
            pass
            
    def addRole(self, person, role):
        if person not in self.personnel:
            print(f"ERROR: {person} does not exist. Create an entry for {person} with Personnel()")
        else:
            person.addRole(role)
            
    def addAppliance(self, appliance):
        if type(appliance) != Appliance:
            print(f"ERROR: {appliance} does not exist. Create {appliance} using Appliance()")
        elif appliance not in self.appliances:
            self.appliances.append(appliance)
        else:
            pass
            
    def setRule(self, appliance, rule):
        if appliance not in self.appliances:
            print(f"ERROR: {appliance} does not exist. Create {appliance} using Appliance()")
        else:
            appliance.setRule(rule)
            
    def setPriority(self, appliance, priority):
        if appliance not in self.appliances:
            print(f"ERROR: {appliance} does not exist. Create {appliance} using Appliance()")
        else:
            appliance.setPriority(priority)
            
    def save(self):
        if not self.fileName:
            self.fileName = f"Rota {self.rota}"
        if not self.rootDir:
            self.rootDir = os.path.abspath(".")
        data = {self.rota: self.personnel}
        with open(os.path.abspath(os.path.expanduser(os.path.join(self.rootDir, self.fileName))), 'wb') as f:
            pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
            
    def load(self):
        if not os.path.abspath(os.path.expanduser(os.path.join(self.rootDir, self.fileName))):
            print("File does not exist. Creating new rota.")
            self.personnel = []
        else:
            with open(os.path.abspath(os.path.expanduser(os.path.join(self.rootDir, self.fileName))), 'rb') as f:
                data = pickle.load(f)
            self.rota = list(data)[0]
            self.personnel = list(data.values())[0]
        
        
class Personnel:
    def __init__(self, name, role=None):
        self.ID = 0
        self.__name__, self._role = name, role
        self.role = None if not self._role else self._role.role
        
    def addRole(self, role):
        if type(role) != Role:
            print(f"ERROR: {role} does not exist. Create {role} with Role()")
class Role:
    def __init__(self, name: str, constraint: Union[dict, list, str, None]=None, rule: bool=False, inherit: [list, Role, None]=None):
        self.role = name

        if type(rule) is not bool:
            raise TypeError("Only boolean rules are allowed")

        if constraints:
            if type(constraints) is dict:
                for i, j in constraints:
                    if type(j) is not bool:
                        raise TypeError("Only boolean rules are allowed")
                    self._constraints = constraint
            elif type(constraints) is list:
                self._constraints = {i: rule for i in list}
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



    def __repr__(self):
        return f"ROLE: {self.role}\nRULE: {self.constraints if self.constraints else 'NONE'}"

    def changeName(self, newName):
        self.__name__ = str(newName)
        
        
class Appliance:
    def __init__(self, name):
        self.__name__ = name
        self.rules, self.priority = None, None
        
    def setRules(self, rules):
        self.rules = rules
    
    def setPriority(self, priority):
        self.priority = priority
        

class Role:
    def __init__(self, role):
        self.role = role
        self.constraints = {}
        
    def _rules(self, constraint):
        self.constraints.update(constraint)
    
    
    
    
    
    
    
    
    
    
    
    
    