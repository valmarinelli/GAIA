# -*- coding: utf-8 -*-
"""
From Python 3 FAQ: How do I share global variables across modules?

The canonical way to share information across modules within a single program
is to create a special module (often called config or cfg). Just import the
config module in all modules of your application; the module then becomes
available as a global name. Because there is only one instance of each module,
any changes made to the module object get reflected everywhere.

To see versions and changelog, open the __init__.py

"""
dev_handle = 0
spectraldata = [0.0] * 2048
alambda = [0.0] * 2048
date = '2018-01-01'
serial = 'demo'