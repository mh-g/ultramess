# ultramess
Program to access two Ultramess (Sharky 775) and one Logarex LK13B via ZVEI interfaces

System environment:
- Raspberry Pico W
- Micropython
- dual optical ZVEI interfaces (model Volkszähler, search for "Lesekopf Hichi" on Ebay, or https://www.ebay.de/itm/285350331996)

Wiring diagram:
- Pico W pin <-> external
- 1 (GP0) <-> Volkszähler #0, TX
- 2 (GP1) <-> Volkszähler #0, RX
- 3 (GND) <-> Volkszähler #0, GND, and Volkszähler #1, GND, and Volkszähler #2, GND
- 6 (GP4) <-> Volkszähler #1, TX
- 7 (GP5) <-> Volkszähler #1, RX
- 16 (GP12) <-> Volkszähler #2, TX
- 17 (GP13) <-> Volkszähler #2, RX
- 36 (3V3OUT) <-> Volkszähler #0, VCC, and Volkszähler #1, VCC, and Volkszähler #2, VCC

Relevant documentation:
- https://www.molline.de/fileadmin/content/content/Bilder/produkte_waerme_kaelte/Kompakt_Ultraschall/Ultramess_H_Waermezaehler/M-Bus_Protokoll_Ultramess_H.pdf
  - (Though it is not really sufficient to implement on its own.)
- https://github.com/ganehag/pyMeterBus to do the parsing of the received data

This is work in progress.

Steps to follow:
- None

Steps most likely not to follow:
- data parsing on Pico W, but on a Raspberry Pi with the database intended for storing the data
