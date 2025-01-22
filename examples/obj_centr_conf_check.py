import pm4py
from pm4py.algo.discovery.ocel.otg import algorithm as otg_discovery
from pm4py.algo.discovery.ocel.etot import algorithm as etot_discovery
from pm4py.algo.conformance.ocel.ocdfg import algorithm as ocdfg_conformance
from pm4py.algo.conformance.ocel.otg import algorithm as otg_conformance
from pm4py.algo.conformance.ocel.etot import algorithm as etot_conformance


def execute_script():
    ocel = pm4py.read_ocel("../tests/input_data/ocel/ocel_order_simulated.csv")

    # subset that we consider as normative
    ocel1 = pm4py.sample_ocel_connected_components(ocel, 1)
    # subset that we use to extract the 'normative' behavior
    ocel2 = pm4py.sample_ocel_connected_components(ocel, 1)

    # object-centric DFG from OCEL2
    ocdfg2 = pm4py.discover_ocdfg(ocel2)
    # OTG (object-type-graph) from OCEL2
    otg2 = otg_discovery.apply(ocel2)
    # ETOT (ET-OT graph) from OCEL2
    etot2 = etot_discovery.apply(ocel2)

    # conformance checking
    print("== OCDFG")
    diagn_ocdfg = ocdfg_conformance.apply(ocel1, ocdfg2)
    print(diagn_ocdfg)

    print("\n\n== OTG")
    diagn_otg = otg_conformance.apply(ocel1, otg2)
    print(diagn_otg)

    print("\n\n== ETOT")
    diagn_etot = etot_conformance.apply(ocel1, etot2)
    print(diagn_etot)


if __name__ == "__main__":
    execute_script()


if __name__ == "__main__":
    execute_script()
