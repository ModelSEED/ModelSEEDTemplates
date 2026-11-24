"""Draft builds (MSBuilder.build_base_model, same call as build_prfba_community_models._build_one) of curated
methanogen genomes against the pristine v7.0 Archaea template and against the patched copy, with the genome's RAST
strings either as the project loads them (whole) or split the way ModelSEEDpy's RAST path splits them
(modelseedpy.core.rast_client.split_annotation). Writes build_results.json next to this script; nothing else.
"""
import json
import re
import sys
import time

import os
S = os.path.dirname(os.path.abspath(__file__))
# the community-modeling project whose genome loader and genome objects the builds use
PROJ = os.environ.get("CODIF_PROJECT", "/home/freiburger/Documents/codiffusion_bioreactor")
REPO = os.path.dirname(os.path.dirname(S))
sys.path.insert(0, PROJ)

from load_genomes_to_modelseedpy import GenomeLoader  # noqa: E402
from modelseedpy.core.msbuilder import MSBuilder  # noqa: E402
from modelseedpy.core.mstemplate import MSTemplateBuilder  # noqa: E402
from modelseedpy.core.rast_client import split_annotation  # noqa: E402

MEMBERS = {"Methanobacterium.3": "09ee5eb3e6c726c7c8242f6e97453fc2",
           "Methanobacterium.16": "d6a202591a42fa999f25af7a7aefcffd",
           "Methanobacterium.1": "0fec351445f84bd482075ceda6123f46"}
PROBE = {"Methanobacterium.3": [1253, 1930, 1024, 1017, 1884, 372, 963, 1052, 964, 1526, 2004],
         "Methanobacterium.16": [837, 414, 463, 348, 95, 477, 510, 778],
         "Methanobacterium.1": [937, 602, 793, 799, 423, 988, 629, 470, 326]}
TARGETS = ["rxn00786_c0", "rxn00549_c0", "rxn07847_c0", "rxn03643_c0", "rxn40405_c0", "rxn00097_c0",
           "rxn00192_c0", "rxn01636_c0", "rxn01300_c0", "rxn00278_c0", "rxn02914_c0", "rxn00424_c0", "rxn00102_c0"]
TPL = {"pristine": os.environ.get("PRISTINE_TEMPLATE", f"{S}/main_v7.0_ArchaeaTemplateV6.json"),  # main 2294299 (git show)
       "patched": f"{REPO}/templates/v7.0/ArchaeaTemplateV6.json"}


def v7e_gene_rxns(member, gid, genes):
    txt = open(f"{PROJ}/models_v7e/{member}.xml").read()
    lab2id = {}
    for m in re.finditer(r"<fbc:geneProduct ([^>]*)>", txt):
        a = dict(re.findall(r'(\S+?)="([^"]*)"', m.group(1)))
        lab2id[a.get("fbc:label")] = a.get("fbc:id")
    g2r = {}
    for rid, body in re.findall(r'<reaction [^>]*id="([^"]+)"(.*?)</reaction>', txt, re.S):
        for gp in re.findall(r'fbc:geneProduct="([^"]+)"', body):
            g2r.setdefault(gp, set()).add(rid[2:] if rid.startswith("R_") else rid)
    return {g: sorted(g2r.get(lab2id.get(f"G_{gid}_{g}"), [])) for g in genes}


def main():
    t0 = time.time()
    loader = GenomeLoader(genome_dir=f"{PROJ}/synthetic_genomes_54d1150/genome_objects")
    tpls = {k: MSTemplateBuilder.from_dict(json.load(open(p))).build() for k, p in TPL.items()}
    print(f"templates built {time.time() - t0:.0f}s", flush=True)
    res = {}
    for member, gid in MEMBERS.items():
        res[member] = {"v7e_draft": v7e_gene_rxns(member, gid, PROBE[member])}
        for split in (False, True):
            for tk, tpl in tpls.items():
                loader._msgenomes.clear()
                msg = loader.get_msgenome(gid, printing=False)
                if split:
                    for f in msg.features:
                        terms = f.ontology_terms.get("RAST", [])
                        parts = []
                        for t in terms:
                            for p in split_annotation(t):
                                p = p.strip()
                                if p and p not in parts:
                                    parts.append(p)
                        f.ontology_terms["RAST"] = parts
                m = MSBuilder(msg, tpl, name=member).build_base_model(member, "0", True, False)
                key = f"{tk}|{'split' if split else 'whole'}"
                gene_rx = {}
                for g in PROBE[member]:
                    gname = f"{gid}_{g}"
                    gene_rx[g] = sorted(r.id for r in m.genes.get_by_id(gname).reactions) if gname in m.genes else []
                tgt = {r: (m.reactions.get_by_id(r).gene_reaction_rule.replace(gid + "_", "") if r in m.reactions else None)
                       for r in TARGETS}
                res[member][key] = {"n_reactions": len(m.reactions), "n_genes": len(m.genes), "gene_reactions": gene_rx,
                                    "targets_gpr": tgt}
                print(f"{member} {key}: {len(m.reactions)} rxns, {len(m.genes)} genes ({time.time() - t0:.0f}s)", flush=True)
    json.dump(res, open(f"{S}/build_results.json", "w"), indent=1)


if __name__ == "__main__":
    main()
