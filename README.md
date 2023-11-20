# ultramess
Program to access two Ultramess (Sharky 775) via ZVEI interfaces

System environment:
- Raspberry Pico W
- Micropython
- dual optical ZVEI interfaces (model Volkszähler, search for "Lesekopf Hichi" on Ebay, or https://www.ebay.de/itm/285350331996)

Relevant documentation:
- https://www.molline.de/fileadmin/content/content/Bilder/produkte_waerme_kaelte/Kompakt_Ultraschall/Ultramess_H_Waermezaehler/M-Bus_Protokoll_Ultramess_H.pdf
  - (Though it is not really sufficient to implement on its own.)
- https://github.com/ganehag/pyMeterBus to do the parsing of the received data

This is work in progress. Steps to follow:
- data transfer via MQTT
- possibly extension with a third ZVEI interface to LOGAREX LK13B to extract electrical power data
