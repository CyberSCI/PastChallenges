import tempfile
from types import SimpleNamespace as SN
from boxdetect import config
from boxdetect.pipelines import get_checkboxes
#from ballotscanner.database import Votes
from PIL import Image
from pyzbar import pyzbar
from io import BytesIO
import cv2
import numpy
import os

RESERVED_TYPECODES = [
    '000001',      # Test confirmation, respond with confirmation
    '000002',      # Return current count of ballots processed
    '000003',      # Return current vote counts
    '000099',      # Administrative mode
]

SEQUENCE = [
    'ONION',
    'CARROT',
    'POTATO',
    'CHEESE',
    'PEAS'
]


def barcodeFilterType(dec):
    return dec.type == 'CODE39'


def process(ballotcode, app, data):
    precinct, typecode = ballotcode.split("-")
    typecode = typecode[:len(typecode) - 1]
    
    #print(f"Ballot Precinct: {precinct}\nBallot Typecode: {typecode}")

    if precinct != app.config['SCANNER_PRECINCT']:
        #print(f"Precinct on ballot ({precinct}) does not match that configured for this scanner {app.config['SCANNER_PRECINCT']}")
        return SN(message='ALARM',code=401)

    if typecode in RESERVED_TYPECODES:
        if typecode == RESERVED_TYPECODES[1]:
            return SN(message='', code=1)
        elif typecode == RESERVED_TYPECODES[2]:
            return SN(message='', code=2)
        elif typecode == RESERVED_TYPECODES[3]:
            adminep = app.config['ADMIN_ENDPOINT']
            return SN(message='', code=302, location=f'/adm/{adminep}')

    tballotfd, tballotpath = tempfile.mkstemp(suffix='.ballot')

    with os.fdopen(tballotfd, 'wb+') as f:
        f.write(data)
    
    cfg = config.PipelinesConfig()
    cfg.width_range = (30,56)
    cfg.height_range = (30,56)
    cfg.scaling_factors = [0.7]
    cfg.wh_ratio_range = (0.7, 1.7)
    cfg.dilation_iterations = 1

    checkboxes = get_checkboxes(tballotpath, cfg)

    os.unlink(tballotpath)

    votes = [0 for _ in range(len(SEQUENCE))]
    ctr = 0
    voteArr = []
    for box in checkboxes:
        checked = box[1]
        print(box)
        if checked:
            votes[ctr] = 1
            voteArr.append(SEQUENCE[ctr])

        ctr += 1

    if len(voteArr) <1:
        voteText = "[NO VOTE DETECTED]"
    else:
        voteText = ", ".join(voteArr)

    if typecode == RESERVED_TYPECODES[0]:
        testflag = app.config['TESTING_FLAG']
        return SN(message=f"""
TEST BALLOT FUNCTIONING AND SCANNED.
PRECINCT CODE: {app.config['SCANNER_PRECINCT']}
THIS TEST BALLOT VOTED FOR: {voteText}
FLAG: {app.config['TESTING_FLAG']}""", code=200)

    return SN(message='', code=0, votes=votes)


MAXDEPTH = 15
def findBarcode(img, depth=0):
    # For debugging purposes only
    #img.save(f"/tmp/barcode_{depth}.png")

    imgarr = BytesIO()
    img.save(imgarr, format='PNG')

    npic = numpy.asarray(bytearray(imgarr.getvalue()), dtype="uint8")
    cvimg = cv2.imdecode(npic, cv2.IMREAD_GRAYSCALE)
    _, bnwimg = cv2.threshold(cvimg, 127, 255, cv2.THRESH_BINARY)

    # For debugging purposes only
    #bnw = Image.fromarray(bnwimg)
    #bnw.save(f"/tmp/barcode_{depth}_bnw.png")

    barcodes = pyzbar.decode(bnwimg, symbols=[pyzbar.ZBarSymbol.CODE39])

    if len(barcodes) < 1:
        if depth >= MAXDEPTH:
            return None

        width, height = img.size

        #print(f"Image size: {width}x{height}")

        minHeight = 500
        coderatio = 3//1.5
        ctop = 0
        cright = width
        cleft = (width / 12)
        cbot = height - (height / 12) * coderatio

        #print("Cropping to:", (cleft, ctop, cright, cbot))

        cropped = img.copy().crop((cleft, ctop, cright, cbot))

        """
        rszHeight = cbot
        if rszHeight < minHeight:
            rszHeight = minHeight
            rszWidth = int(rszHeight * coderatio)

            print(f"Resizing to {rszWidth}x{rszHeight}")
            cropped = cropped.resize((rszWidth, rszHeight), Image.LANCZOS)
        """

        return findBarcode(cropped, depth + 1)
    else:
        filteredcodes = list(filter(barcodeFilterType, barcodes))
        #print(filteredcodes)

        if len(filteredcodes) < 1 and depth >= MAXDEPTH:
            return None
        else:
            return filteredcodes[0]

