from .bias import Bias
from .dark import Dark
from .defects import Defects
from .detcal import DetCal
from .eper import Eper
from .fe55 import Fe55
from .gain import Gain
from .gainmap import GainMap
from .linearity import Linearity
from .metrology import Metrology
from .pocketpump import PocketPump
from .prnu import Prnu
from .ptc import Ptc
from .qe import QE
from .ramp import Ramp
from .superflat import Superflat


def load_testers(testers="all"):
    """
    Load the testers as azcam tools.
    """

    if testers == "all":
        bias = Bias()
        dark = Dark()
        defects = Defects()
        detcal = DetCal()
        eper = Eper()
        fe55 = Fe55()
        gain = Gain()
        gainmap = GainMap()
        linearity = Linearity()
        metrology = Metrology()
        pocketpump = PocketPump()
        prnu = Prnu()
        ptc = Ptc()
        qe = QE()
        ramp = Ramp()
        superflat = Superflat()

    return
