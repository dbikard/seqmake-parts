"""Map GenBank/INSDC feature types to Sequence Ontology accessions.

The Sequence Ontology (SO, https://www.ebi.ac.uk/ols4/ontologies/so) is the
INSDC-aligned controlled vocabulary for sequence features. Parts and their
sub-features carry a SO accession so a part's functional class is unambiguous
and portable - written as a GenBank ``/db_xref="SO:..."`` and surfaced as the
catalog manifest's ``so_term``. This typing is what keeps functionally distinct
parts distinct (e.g. a promoter SO:0000167 is not a ribosome entry site
SO:0000139).

Shared by ``build_catalog.py`` (read: derive a feature's so_term) and
``publish_part.py`` (write: stamp the main feature's ``/db_xref``), so the two
sides cannot drift. Pure-Python (no BioPython) so either can import it cheaply.

Accessions verified against OLS4 (SO, 2024-11).
"""
from __future__ import annotations

# regulatory_class -> (SO accession, SO name). The INSDC regulatory_class
# vocabulary is itself derived from SO, so this is a 1:1 mapping.
SO_BY_REG: dict[str, tuple[str, str]] = {
    "minus_35_signal": ("SO:0000175", "minus_35_signal"),
    "minus_10_signal": ("SO:0000176", "minus_10_signal"),
    "ribosome_binding_site": ("SO:0000139", "ribosome_entry_site"),
    "promoter": ("SO:0000167", "promoter"),
    "terminator": ("SO:0000141", "terminator"),
    "TATA_box": ("SO:0000174", "TATA_box"),
    "operator": ("SO:0000057", "operator"),
    "enhancer": ("SO:0000165", "enhancer"),
    "silencer": ("SO:0000625", "silencer"),
    "attenuator": ("SO:0000140", "attenuator"),
    "polyA_signal_sequence": ("SO:0000551", "polyA_signal_sequence"),
}

# feature type -> (SO accession, SO name)
SO_BY_TYPE: dict[str, tuple[str, str]] = {
    "promoter": ("SO:0000167", "promoter"),
    "CDS": ("SO:0000316", "CDS"),
    "terminator": ("SO:0000141", "terminator"),
    "RBS": ("SO:0000139", "ribosome_entry_site"),
    "rep_origin": ("SO:0000296", "origin_of_replication"),
    "oriT": ("SO:0000724", "oriT"),
    "protein_bind": ("SO:0000410", "protein_binding_site"),
    "protein_domain": ("SO:0000417", "polypeptide_domain"),
    "misc_RNA": ("SO:0000655", "ncRNA"),
    "regulatory": ("SO:0005836", "regulatory_region"),
    "minus_35_signal": ("SO:0000175", "minus_35_signal"),
    "minus_10_signal": ("SO:0000176", "minus_10_signal"),
    "sig_peptide": ("SO:0000418", "signal_peptide"),
    "transit_peptide": ("SO:0000725", "transit_peptide"),
    "propeptide": ("SO:0001062", "propeptide"),
    "mat_peptide": ("SO:0000419", "mature_protein_region"),
    "gene": ("SO:0000704", "gene"),
    "stem_loop": ("SO:0000313", "stem_loop"),
    "binding": ("SO:0000409", "binding_site"),
    "misc_binding": ("SO:0000409", "binding_site"),
    "primer_bind": ("SO:0005850", "primer_binding_site"),
    "misc_recomb": ("SO:0000298", "recombination_feature"),
    "disulfide_bond": ("SO:0001088", "disulfide_bond"),
    "modified_residue": ("SO:0001089", "post_translationally_modified_region"),
    "misc_feature": ("SO:0000110", "sequence_feature"),
}


def so_for(feature_type: str, regulatory_class: str | None = None,
           label: str | None = None) -> tuple[str, str] | None:
    """Return ``(SO_accession, SO_name)`` for a feature, or ``None`` if unmapped.

    ``regulatory_class`` is the most specific signal; otherwise the feature
    type, with a few label-based refinements (the +1/TSS, operators, and a
    Shine-Dalgarno within an RBS).

    Example:
        >>> so_for("regulatory", regulatory_class="minus_35_signal")
        ('SO:0000175', 'minus_35_signal')
        >>> so_for("RBS")
        ('SO:0000139', 'ribosome_entry_site')
    """
    if regulatory_class and regulatory_class in SO_BY_REG:
        return SO_BY_REG[regulatory_class]
    lab = (label or "").lower()
    if lab.startswith("+1") or "transcription start" in lab or lab.strip() == "tss":
        return ("SO:0000315", "TSS")
    if feature_type == "protein_bind" and (
        "operator" in lab or any(t in lab for t in ("teto", "laco", "arao", "pho"))
    ):
        return ("SO:0000057", "operator")
    # Type at the functional-class level: an RBS is ribosome_entry_site
    # (SO:0000139), matching how a promoter is SO:0000167 rather than the more
    # specific bacterial_RNApol_promoter. Shine_Dalgarno_sequence (SO:0000552) is
    # a sub-element - use it only on an explicit /db_xref or a dedicated
    # sub-feature, never derived from an RBS feature's label.
    return SO_BY_TYPE.get(feature_type)
