"""miscellaneous tools for the simulation logger"""

global PRINT
def PRINT(* args): pass

def verbose_print(* args):
    """a more verbose print"""
    for arg in args:
        print arg,
    print

def simulation_end():
    print "logger is now exiting"
    import os
    os._exit(0)
