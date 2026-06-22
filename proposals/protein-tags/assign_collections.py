#!/usr/bin/env python3
"""Assign the 5 protein-tag category collections to each tag part's main feature.

Idempotent: sets feature[0].qualifiers["collection"] to the mapped list (overwrites,
so re-running after more parts land is safe). collections.json supplies the prose.
A part may belong to several collections (FLAG = affinity + epitope, etc.).
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

MAP = {
    # affinity purification handles
    "6xHis": ["affinity-tags"],
    "FLAG": ["affinity-tags", "epitope-tags"],
    "GST": ["affinity-tags", "solubility-tags"],
    "MBP": ["affinity-tags", "solubility-tags"],
    "Strep_tag": ["affinity-tags"],
    "Twin_Strep_tag": ["affinity-tags"],
    "S-tag": ["affinity-tags"],
    "CBP_tag": ["affinity-tags"],
    "SBP_tag": ["affinity-tags"],
    "E-tag": ["affinity-tags", "epitope-tags"],
    # epitope / detection
    "HA": ["epitope-tags"],
    "Myc": ["epitope-tags"],
    "T7_tag": ["epitope-tags"],
    "V5_tag": ["epitope-tags"],
    "VSVG_tag": ["epitope-tags"],
    "ALFA_tag": ["epitope-tags"],
    "Spot_tag": ["epitope-tags"],
    "BC2_tag": ["epitope-tags"],
    # solubility fusion partners
    "Trx_tag": ["solubility-tags"],
    "NusA": ["solubility-tags"],
    "SUMO": ["solubility-tags"],
    # protease cleavage sites + the SUMO protease
    "TEV_site": ["protease-cleavage-sites"],
    "thrombin_site": ["protease-cleavage-sites"],
    "enterokinase_site": ["protease-cleavage-sites"],
    "HRV3C_site": ["protease-cleavage-sites"],
    "FactorXa_site": ["protease-cleavage-sites"],
    "Ulp1": ["protease-cleavage-sites"],
    # conjugation / self-labeling systems
    "AviTag": ["conjugation-tags"],
    "birA": ["conjugation-tags"],
    "SpyTag": ["conjugation-tags"],
    "SpyTag002": ["conjugation-tags"],
    "SpyTag003": ["conjugation-tags"],
    "SpyCatcher": ["conjugation-tags"],
    "SnoopTag": ["conjugation-tags"],
    "SnoopCatcher": ["conjugation-tags"],
    "SNAP_tag": ["conjugation-tags"],
    "LPETG_tag": ["conjugation-tags"],
}


def main():
    done, missing = [], []
    for slug, colls in MAP.items():
        fp = ROOT / "parts" / "validated" / f"{slug}.json"
        if not fp.exists():
            missing.append(slug)
            continue
        d = json.loads(fp.read_text(encoding="utf-8"))
        d["features"][0].setdefault("qualifiers", {})["collection"] = colls
        fp.write_text(json.dumps(d, indent=2) + "\n", encoding="utf-8")
        done.append(slug)
    print(f"assigned {len(done)} parts; missing (not yet validated): {missing}")


if __name__ == "__main__":
    main()
