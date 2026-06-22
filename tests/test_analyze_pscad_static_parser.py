import xml.etree.ElementTree as ET

from scripts.analyze_pscad_ibr_type3_mapping import element_has_term


def test_element_has_term_uses_exact_signal_names():
    elem = ET.Element("param", {"name": "Units", "value": "MW"})
    assert not element_has_term(elem, "UN")
    assert element_has_term(elem, "Units")


def test_element_has_term_handles_namespaced_defn():
    elem = ET.Element("User", {"defn": "Type3_Ave_Nov_2018:Type3_WTG_Avg"})
    assert element_has_term(elem, "Type3_WTG_Avg")
