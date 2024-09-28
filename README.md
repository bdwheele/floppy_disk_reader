# floppy_disk_reader
Floppy disk reader w/case

# Physical Device

## Bill of Materials
|Qty| Description | Price |
|---|-------------|---|
| 1 | GreaseWeazle v4.1 (https://www.ebay.com/itm/255252124132) | $54.30 |
| 1 | 3.5" Floppy Drive (https://www.ebay.com/itm/156317606798) | $34.00 |
| 1 | Floppy Power Cable 4pk (https://www.amazon.com/dp/B0CLD7YRWC) | $7.88 |
| 1 | Floppy Data Cable 2pk (https://www.amazon.com/dp/B092VD1QQL) | $14.35 |
| 1 | USB-C Cable (https://www.amazon.com/dp/B01GGKZ2SC) | $6.99 |
|   | Total   | $117.52 |

### Not included
* I printed the case for a material cost of around $4 and approximately 
  4 hours of printing time.
* Screws, solder, heatshrink tubing, etc.  These were just laying around.

### Parts not used
* Only one of the data cables was used
* Two of the power cables were used


## Construction

### Case
Print the STL models in the case directory using these settings:
* PLA
* 0.40 nozzle
* 0.20 layer height
* 15% infill
* grid supports, everywhere
     
Using a Prusa MK4 with Input Shaper, each case half takes slighly more than 2 hours

### Power Cable Modification
The four power cables each have a standard molex connector on one end and a 3.5" floppy connector on the other.  The greaseweazle has a floppy power connector on it so the cable we need must have the same connector on both ends.

* On two of the cables, cut the cable around 1.5" from molex connector end.
* Solder like wires together (red <-> red, yellow <-> yellow, and 2 black <-> black) using heatshrink tubing to avoid shorting.

### Assembly

* Remove the greaseweazle from the supplied case
* Transfer the greaseweazle to the bottom of the new case and attach it using the same 4 screws, aligning the USB C port with the hole in the back of the case.
* Connect the modified power cable to the greaseweazle and the floppy drive.
* Connect the data cable to the greaseweazle and the floppy drive, taking care to
align pin 1 on both devices.  In my case the twist end was near the greaseweazle.
* Remove the write enable jumper on the greaseweazle.
* Place the floppy drive into the top half of the case and use the two front screws to secure them together.
* Fold the two halves of the case together, ensuring the cables do not get into a bind.
* Insert the rear screws through the case into the floppy drive .


# Software

pyinstaller --add-data fluxengine.fedora40:. --add-data fluxengine.exe:.
