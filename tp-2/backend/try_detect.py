import sys

import cv2

from docscan import read_photo
from docscan.scanner import Scanner


with open(sys.argv[1], "rb") as f:
    photo = read_photo(f.read())

scanned, corners = Scanner().scan(
    photo.image,
    color_mode="bw",
    color_correction=True,
    soften_colors=0.5,
)

print(corners)
cv2.imwrite("scan_result.png", scanned)
print("Guardé el resultado en scan_result.png")

out = photo.image.copy()
for i, (x, y) in enumerate(corners):
    cv2.circle(out, (int(x), int(y)), 25, (0, 0, 255), -1)
    cv2.putText(
        out,
        str(i),
        (int(x) + 30, int(y)),
        cv2.FONT_HERSHEY_SIMPLEX,
        2,
        (0, 255, 0),
        4,
    )
cv2.imwrite("debug_corners.png", out)