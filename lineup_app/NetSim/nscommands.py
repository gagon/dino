import netsim as ns

gap=ns.read_gap_file()
ns.DoSet(gap,"seps/kpc/masked",0)
ns.DoSet(gap,"seps/u2/masked",0)
ns.DoSet(gap,"seps/u3/masked",0)
ns.build_network()
