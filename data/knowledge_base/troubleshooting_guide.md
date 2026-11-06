# Pearlz Home Systems — Troubleshooting Guide
**Document ID:** GUIDE-TS-2026.1  
**Version:** 2026.1  
**Last updated:** 15 January 2026  
**Applies to:** AquaPearl 300, AquaPearl 500 Pro (alert codes), AeroPearl Mini (where noted)

## Escalation criteria — do not attempt DIY
Stop and contact an Authorised Service Partner if you observe:
- Burning smell, smoke, or melted plastic
- Electrical shock sensation from the chassis
- Continuous water leak that does not stop after closing the inlet valve
- Crack in a pressurised housing

## Symptom → cause → action table

| # | Symptom | Probable cause | Customer action |
|---|---|---|---|
| 1 | No power / blank display | Unplugged, tripped breaker, faulty socket | Verify socket with another device; try a different socket; check fuse |
| 2 | Low water flow | Clogged sediment pre-filter; kinked tubing | Replace sediment filter; straighten tubing; check inlet pressure |
| 3 | Leaking base | Loose drain clamp; cracked elbow fitting | Close inlet; tighten clamps; if crack visible, escalate — do not glue |
| 4 | Bad / strange taste after filter change | Residual carbon fines; incomplete flush | Run first-run flushing procedure (see Installation Guide); discard first 2 tanks |
| 5 | Continuous pump running | Float sensor stuck; tank not filling | Power cycle; check tank sensor free movement; escalate if persists |
| 6 | Three short beeps then stop | Error **E-03** — sediment pre-filter saturation | Replace sediment pre-filter cartridge; press and hold RESET 5 seconds |
| 7 | Blinking red LED (status) | Error **E-05** — leak sensor wet | Close inlet; dry base sensor; inspect for leaks; RESET after dry |
| 8 | TDS reading high on display | Exhausted RO membrane; inlet TDS spike | Check inlet TDS; replace RO membrane if due; do not drink until resolved |
| 9 | Noisy pump / rattling | Air in line; pump mounting loose | Bleed air via flush valve; tighten mounts; escalate if metal grinding |
| 10 | App will not pair | Bluetooth off; unit not in pairing mode | Enable Bluetooth; hold PAIR 3s until blue blink; reboot phone |
| 11 | Two long beeps | Error **E-01** — inlet valve timeout | Open inlet tap fully; check for closed stopcock |
| 12 | Five rapid beeps | Error **E-08** — UV lamp failure (500 Pro) | Escalation only — UV lamp is not customer-replaceable |
| 13 | Weak airflow (AeroPearl) | Clogged HEPA; fan obstruction | Replace HEPA; vacuum intake grille |
| 14 | Display shows E-02 | Tank full sensor fault | Empty tank; inspect sensor; escalate if repeats |
| 15 | Display shows E-04 | Low inlet pressure | Confirm inlet pressure within 0.1–0.4 MPa; install booster if needed |
| 16 | Display shows E-06 | Over-temperature electronics | Unplug 30 minutes; ensure 10 cm clearance; escalate if repeats |
| 17 | Display shows E-07 | Communication fault control↔pump | Power cycle; escalate if persists — do not open electronics |
| 18 | Unit runs but no purified water | Shut-off valve closed; RO clogged | Open pure-water tap path; check membrane age |

## Audible alert codes (AquaPearl 500 Pro)
| Code | Pattern | Meaning | First action |
|---|---|---|---|
| E-01 | 2 long beeps | Inlet valve timeout | Open inlet; check stopcock |
| E-02 | 1 long + 1 short | Tank full sensor fault | Empty tank; inspect sensor |
| E-03 | 3 short beeps | Sediment pre-filter saturation | Replace pre-filter; hold RESET 5s |
| E-04 | 4 short beeps | Low inlet pressure | Verify pressure range |
| E-05 | Blinking red LED (+ optional beep) | Leak sensor wet | Dry sensor; find leak |
| E-06 | Continuous tone 2s | Over-temperature | Unplug; cool down |
| E-07 | Alternating beeps | Comm fault | Power cycle; escalate |
| E-08 | 5 rapid beeps | UV lamp failure | Escalate — no DIY |

**Note:** Firmware 2.4 changed the meaning of E-06. See Product Changelog. Units on firmware 2.3 and earlier used E-06 for “filter due soon” instead of over-temperature. Check firmware version in the Pearlz app before advising.

## Three beeps — customer language mapping
Customers often say “beeping three times” or “keeps beeping three times and then stops”. On AquaPearl 500 Pro this maps to **E-03 (sediment pre-filter saturation)**. Recommended action: replace the sediment pre-filter cartridge, then press and hold the RESET button for five seconds to clear the alert.
