from __future__ import annotations

import tempfile
from pathlib import Path
from xml.sax.saxutils import escape

from .sampling import SamplePoint


def render_point_kml(point: SamplePoint, range_meters: int = 1200) -> str:
    name = escape(point.id)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>{name}</name>
    <Placemark>
      <name>{name}</name>
      <Point>
        <coordinates>{point.longitude:.8f},{point.latitude:.8f},0</coordinates>
      </Point>
    </Placemark>
    <LookAt>
      <longitude>{point.longitude:.8f}</longitude>
      <latitude>{point.latitude:.8f}</latitude>
      <altitude>0</altitude>
      <heading>0</heading>
      <tilt>0</tilt>
      <range>{range_meters}</range>
      <altitudeMode>relativeToGround</altitudeMode>
    </LookAt>
  </Document>
</kml>
"""


def write_temp_kml(point: SamplePoint, range_meters: int = 1200) -> Path:
    temp = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".kml",
        prefix="earth-imagery-watcher-",
        delete=False,
    )
    with temp:
        temp.write(render_point_kml(point, range_meters=range_meters))
    return Path(temp.name)
