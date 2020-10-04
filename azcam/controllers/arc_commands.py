"""
Client-side commands for ARC controller.
"""

import azcam


def stop_idle():
    """
    Stop idle clocking.
    """

    s = "controller.stop_idle"
    azcam.api.rcommand(s)

    return


def start_idle():
    """
    Start idle clocking.
    """

    s = "controller.start_idle"
    azcam.api.rcommand(s)

    return


def set_bias_number(BoardNumber, DAC, Type, DacValue):
    """
    Sets a bias value.
    BoardNumber is the controller board number.
    DAC is DAC number.
    Type is 'VID' or 'CLK'.
    DacValue is DAC value for voltage.
    """

    s = 'controller.set_bias_number %d %d "%s" %d' % (BoardNumber, DAC, Type, DacValue)
    azcam.api.rcommand(s)

    return


def write_controller_memory(Type, BoardNumber, Address, value):
    """
    Write a word to a DSP memory location.
    Type is P, X, Y, or R memory space.
    BoardNumber is controller board number.
    Address is memory address to write.
    value is data to write.
    """

    s = 'controller.write_memory "%s" %d %d %d' % (Type, BoardNumber, Address, value)
    azcam.api.rcommand(s)

    return


def read_controller_memory(Type, BoardNumber, Address):
    """
    Read from DSP memory.
    Type is P, X, Y, or R memory space.
    BoardNumber is controller board number.
    Address is memory address to read.
    """

    s = 'controller.read_memory "%s" %d %d' % (Type, BoardNumber, Address)
    azcam.api.rcommand(s)

    return


def board_command(Command, BoardNumber, Arg1=-1, Arg2=-1, Arg3=-1, Arg4=-1):
    """
    Send a specific command to an ARC controller board.
    The reply from the board is not usually 'OK', it is often 'DON' but could be data.
    Command is the board command to send.
    BoardNumber is controller board number.
    ArgN are arguments for Cmd.
    """

    s = 'controller.board_command "%s" %d %d %d %d %d' % (
        Command,
        BoardNumber,
        Arg1,
        Arg2,
        Arg3,
        Arg4,
    )
    azcam.api.rcommand(s)

    return
