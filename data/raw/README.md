# Raw data

Eurostat files are kept exactly as downloaded, compressed with gzip (pandas reads
them directly; to look inside, `gunzip -k file.csv.gz`). Only the file names have
been changed. Downloaded on 14 October 2026.

## comext/  Eurostat Comext DS-045409, EU27 trade by CN8, 2022–2024 (SDMX-CSV)

| File | Original name | Content |
|---|---|---|
| comext_eu27_totals.csv.gz | estat_ds-045409_filtered_en.csv | Partners EXT_EU27_2020 and INT_EU27_2020; imports (flow 1) and exports (flow 2); value in € and quantity in 100 kg |
| comext_imports_by_partner_1.csv.gz | estat_ds-045409_filtered_en (1).csv | Imports, value in €, from 15 countries (CH, CN, GB, IN, JP, KR, TR, US, ...) |
| comext_imports_by_partner_2.csv.gz | estat_ds-045409_filtered_en (2).csv | Imports from 15 countries (AL, BA, BR, CA, MA, MX, ...) |
| comext_imports_by_partner_3.csv.gz | estat_ds-045409_filtered_en (3).csv | Imports from 14 countries (AE, AU, HK, NO, SA, ...) |

Dataset last updated by Eurostat on 15 September 2026. The 44 countries supply
most, not all, extra-EU imports; supplier shares are measured against the
extra-EU total.

## prodcom/  EU production

| File | Origin |
|---|---|
| prodcom_2019_2024.csv.gz | Eurostat Prodcom DS-059358, EU27 sold production, exports, imports by Prodcom code, 2019–2024 (updated 16 Sep 2026) |
| prodcom_2025.csv.gz | Eurostat Prodcom DS-059367, 2025 release under NACE Rev. 2.1 (updated 29 Sep 2026) |
| prodcom_cn_correspondence_2025.xlsx | Prodcom–CN correspondence 2025, Statistics Netherlands (CBS) |
| cn8_prodcom_concordance_magerman.tsv.gz | CN8–Prodcom concordance, Magerman (ULB), 2001–2014; the 2014 version is used |

## legal/  The three positions' product lists, transcribed by hand

| File | Source |
|---|---|
| commission_annex_i.csv | Commission proposal COM(2025) 989, Annex I, as sent to the Council in ST 16973/25 ADD 1 (17 Dec 2025): the replacement iron-and-steel table and the 107-row "combined metal products" table; `ex` = 1 where the code is printed with "ex" |
| council_note1_additions.csv | Council general approach ST 10423/26 (12 Jun 2026), Annex I, NOTE 1: 200 CN8 lines added |
| council_note2_deletions.csv | Same, NOTE 2: three Commission lines deleted |
| parliament_amendment_83.csv | Parliament position P10_TA(2026)0276 (15 Sep 2026), Amendment 83: 276 CN8 lines, with PDF page |
| parliament_broad_entries.csv | Same, Amendments 110 and 135: 24 broad entries. `read_as` turns the non-existent codes 8481 00 and 8483 00 into headings 8481 and 8483 |
| exclusions.csv | Ferro-alloy exceptions (all positions) and the 11 truck lines excluded inside the Commission's "ex 8704" entries (Commission and Council) |
| baseline_regulation_2023_956.csv | Today's CBAM scope, Regulation (EU) 2023/956, Annex I (iron, steel and aluminium) |
| source_text/council_st10423_26_extracted.txt | Text extracted from the Council PDF, for checking the transcription |

Official texts:
Commission https://data.consilium.europa.eu/doc/document/ST-16973-2025-ADD-1/en/pdf ·
Council https://data.consilium.europa.eu/doc/document/ST-10423-2026-INIT/en/pdf ·
Parliament https://www.europarl.europa.eu/doceo/document/TA-10-2026-0276_EN.html
