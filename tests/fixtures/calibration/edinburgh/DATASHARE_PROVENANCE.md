# Edinburgh DataShare provenance

This directory vendors the public dataset "Hydrodynamics of Three Slender
Models Resembling Pacific Canoe Hulls" so the RFC 0042 source-review packet
and validation-fixture extractor have a deterministic, checksum-bound copy.

## Locators

- Landing page: https://datashare.ed.ac.uk/handle/10283/4772
- Persistent identifier: https://doi.org/10.7488/ds/3785
- Bundle download (zip): https://datashare.ed.ac.uk/download/DS_10283_4772.zip

## Access

- Access date: 2026-05-15
- Bundle SHA-256 (`DS_10283_4772.zip`):
  `20fc15671941ffe71619a1796b9a3c121de226f03024f06f69a72e664b06c8ea`

## Vendored files and per-file SHA-256

| File | SHA-256 |
| --- | --- |
| `FixedSink_and_TrimDataAnalysis20221114V15_IMV.xlsx` | `dffbd5d4547c9e1c1f5597d6188dc2a1efffd316ab301451fb818e11a22acade` |
| `Outriggeruntrimmed.igs` | `ef19b28adafaf9022b8290f643828549caa16065abfa646548b74cf01030b526` |
| `README.txt` | `64bb16a0708b0a83f52089baf9296a20f0747a0b923ac2278293c804028a3d41` |
| `license_text` | `b34e17103bfb246f2549fc82a279e6ba28834e0cb42f76a92efc14b72e3a3723` |

## License and attribution

CC BY 4.0. Required attribution string used by the kayakgen registry:

> University of Edinburgh DataShare, Hydrodynamics of Three Slender Models
> Resembling Pacific Canoe Hulls (DOI 10.7488/ds/3785), CC BY 4.0.

The unmodified upstream `license_text` and `README.txt` are vendored beside
this file.

## RFC 0042 scope

Per decision D013 the Edinburgh dataset is reviewed as a
**validation candidate**, capped at `validation_fixture` as the only positive
promotion outcome. It remains
`outside_sea_kayak_calibration_envelope` for any future calibration use; the
Pacific canoe geometry is not in the kayak/surfski envelope kayakgen targets.
