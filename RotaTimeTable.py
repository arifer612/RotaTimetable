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
        else:
            self._role = role
        
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
    
    
    
    
    
    
    
    
    
    
    
    
    