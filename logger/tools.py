"""miscellaneous tools for the simulation logger"""

verbose = False

def PRINT(* args):
    """a more verbose print"""
    if verbose:
        for arg in args:
            print arg,
        print

def set_verbose(status):
    global verbose
    verbose = status

def simulation_end():
    print "logger is now exiting"
    import os
    os._exit(0)
