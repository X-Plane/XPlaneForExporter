import pprint
import itertools
from dataclasses import dataclass, field

trees = (
    "TREE	85	300	78	116	38	3.3	9	18	2	0	broadleaf1",
    "TREE	85	310	78	106	38	3.3	15	20	2	0	broadleaf1_tall",
    "TREE	1	300	82	115	40.7	3.3	8	19	2	0	broadleaf2",
    "TREE	1	310	82	105	40.7	3.3	15	22	2	0	broadleaf2_tall",
    "TREE	325	305	72	110	37	3.3	4	12	2	2	ornamental1",
    "TREE	0	0	70	199	34	3.3	12	15	2	1	palm1",
    "TREE	70	0	67	182	34	3.3	10	12	2	1	palm2",
    "TREE	137	0	55	141	27	3.3	4	8	2	1	snail_tree",
    "TREE	193	0	62	127	32	3.3	3	9	2	1	conifer1",
    "TREE	256	0	65	114	31	3.3	2	6	2	2	fig",
    "TREE	323	0	24	167	12	3.3	2	10	2	11	cypress",
    "TREE	352	0	72	128	34	3.3	20	25	2	1	tall_tropical1",
    "TREE	425	0	66	128	41	3.3	18	24	2	1	tall_tropical2",
    "TREE	163	289	72	128	36	3.3	20	23	2	1	tall_conifer",
    "TREE	236	289	87	101	42	3.3	5	10	2	2	acacia?",
    "TREE	397	273	114	126	63	3.3	4	12	2	0	round_tree",
    "TREE	385	129	127	118	64	3.3	15	20	2	0	plane",
    "TREE	64	192	38	96	20	3.3	1.5	3	2	11	small_cypress	",
    "TREE	106	246	57	39	29	3.3	0.75	2	2	3	shrub_mid_green1",
    "TREE	327	168	56	31	28	3.3	2	4	2	10	ground_palm",
    "TREE	164	263	45	24	23	3.3	0.75	2	2	3	shrub_dark_green1",
    "TREE	210	263	48	24	24	3.3	0.75	2	2	3	shrub_light_green1",
    "TREE	259	263	49	24	24	3.3	0.75	1.5	2	3	shrub_grey",
    "TREE	309	263	46	23	23	3.3	0.75	1.5	2	3	shrub_light_olive",
    "TREE	357	263	27	19	14	3.3	0.75	1.25	2	3	shrub_light_green2",
    "TREE	103	192	57	51	28	3.3	1	2.5	2	3	shrub_dark_green2",
    "TREE	160	192	36	34	18	3.3	0.5	1.5	2	3	shrub_light_green3",
    "TREE	198	192	32	34	16	3.3	0.5	2.0	2	3	shrub_dark_green3",
    "TREE	231	192	43	36	21	3.3	0.5	2.1	2	3	shrub_mid_green2",
    "TREE	275	192	36	31	18	3.4	0.5	2.2	2	3	shrub_mid_green3",
    "TREE	512	467	259	44	129.5	100	1.5	2.0	1	100	wood_fence1a_8m",
    "TREE	768	467	256	44	128	100	1.5	2.0	1	101	wood_fence1b_8m_w_gate",
    "TREE	935	467	35	44	17.5	100	1.5	2.0	1	102	wood_fence1c_gate_only",
    "TREE	512	412	389	52	195	100	1.5	2.0	1	110	wood_fence2a_12m",
    "TREE	512	412	511	52	256	100	1.5	2.0	1	111	wood_fence2b_16m_w_trees",
    "TREE	904	412	120	52	60	100	1.5	2.0	1	112	wood_fence2c_trees_only",
    "TREE	512	365	511	43	256	100	1.5	2.0	1	120	brick_wall1a_16m",
    "TREE	516	307	473	56	236.5	100	2.0	2.0	1	130	wood_fence_3a_14m",
    "TREE	986	307	35	56	17.5	100	2.0	2.0	1	131	wood_fence_3a_gate_only",
    "TREE	512	255	374	50	187	100	1.5	2.0	1	140	white_siding1a_11m",
    "TREE	512	255	511	50	256	100	1.5	2.0	1	141	white_siding1a_16m",
    "TREE	512	210	413	41	207	100	1.5	2.0	1	150	rush_fence1a_12m",
    "TREE	991	210	32	41	16	100	1.5	2.0	1	151	ruah_fence1b_gate_only",
    "TREE	513	160	510	47	255	50	1.25	2.5	1	160	hedge_lt_green_20m",
    "TREE	513	112	510	46	255	50	1.25	2.5	1	160	hedge_dk_green_20m",
    "TREE	0	290	365	41	145	100	2	4	1	12	test_hedge",
)



@dataclass
class TreeStruct:
    s: int
    t: int
    w: int
    h: int
    offset: int
    freq: float
    min_height: float
    max_height: float
    quads: int
    layer_number: int
    notes: str

    def __post_init__(self):
        for attr, factory in type(self).__annotations__.items():
            try:
                setattr(self, attr, factory(getattr(self, attr)))
            except ValueError:
                print("couldn't convert", attr, "with", factory, "factory", "with value ", getattr(self, attr))

@dataclass
class YQuadStruct:
    s:int
    t:int
    width:int
    height:int
    offset_center_x:int
    offset_center_y:int
    quad_width:int # pixels, relative to vertical tree
    elevation:int # pixels, relative to vertical tree
    psi_rotation:float

    def __post_init__(self):
        for attr, factory in type(self).__annotations__.items():
            try:
                setattr(self, attr, factory(getattr(self, attr)))
            except ValueError:
                print("couldn't convert", attr, "with", factory, "factory", "with value ", getattr(self, attr))


real_trees = sorted(
    [
        # (TreeStruct(**dict(zip(args, tree_line.split()[1:])))) for tree_line in trees
        TreeStruct(*tree_line.split()[1:])
        for tree_line in trees
    ],
    key=lambda t: t.layer_number,
)

pprint.pprint(real_trees)

layer_numbers = {t.layer_number for t in real_trees}

layer_numbers_to_total_frequencies = {
        layer_number: sum(t.freq for t in real_trees if t.layer_number == layer_number) for layer_number in layer_numbers
    }
pprint.pprint(layer_numbers_to_total_frequencies)

pprint.pprint([t for t in real_trees if t.layer_number == 0])
