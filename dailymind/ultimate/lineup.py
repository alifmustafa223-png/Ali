import skia, numpy as np
from PIL import Image
from toon import *
surf = skia.Surface(2400, 1100); c = surf.getCanvas()
c.drawPaint(P(C(60, 30, 50)))
looks = [(LADY, dict(hands=[(-60, -230), (40, 120)], mouth="smile", brows="smug", eyes="open")),
         (COLUMBUS, dict(hands=[(-30, 140), (120, 60)], mouth="O", brows="up", eyes="wide")),
         (GARDENER, dict(hands=[(60, -60), (10, 150)], mouth="disgust", brows="angry", eyes="squint")),
         (KING, dict(hands=[(-90, 60), (-40, 80)], mouth="O", brows="up", eyes="wide", lean=-6)),
         (SHOP, dict(hands=[(80, 60), (20, 150)], mouth="smile", brows="flat")),
         (KID, dict(hands=[(40, -110), (30, 150)], mouth="laugh", eyes="closed")),
         (crowd_look(0), dict(mouth="O", eyes="wide", brows="up")), (crowd_look(1), dict(mouth="O", eyes="wide", brows="up"))]
for i, (lk, pose) in enumerate(looks):
    person(c, 150 + i * 300, 1050, 1.15, lk, pose, 0.3)
pine(c, 150 - 60*1.15 - 60*1.15 + 60, 1050 - 235*1.15 - 230*1.15 - 60, 0.9)
Image.fromarray(surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)[:, :, :3]).save("lineup.png")
