#!/usr/bin/env python3

"""
Access package for the bookstore frontend
"""

from fe.access.new_buyer import register_new_buyer
from fe.access.buyer import Buyer
from fe.access.auth import Auth

__all__ = ['register_new_buyer', 'Buyer', 'Auth']
