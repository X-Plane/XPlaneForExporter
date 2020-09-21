A
800
FOREST

SHADER_2D
	TEXTURE ../textures/y_quad_test.png

SCALE_X	512
SCALE_Y	512
SPACING	24 24
RANDOM	20 20


#TREE	<s>	<t>	<w>	<h>	<offset>	<frequency>	<min h>	<max h>	<quads>	<layer>	<notes>
TREE	112	384	98	128	49	100	4	14	1	1	TREE_y_quad_no_offset
#Y_QUAD	<left>	<bottom>	<width>	<height>	<offset_center_x>	<offset_center_y>	<width>	<elevation>	<rotation>
Y_QUAD	110	286	100	98	50	49	98.0	72	0
#TREE	<s>	<t>	<w>	<h>	<offset>	<frequency>	<min h>	<max h>	<quads>	<layer>	<notes>
TREE	0	412	10	100	5	100	10	14	1	2	TREE_y_quad_offset_x
#Y_QUAD	<left>	<bottom>	<width>	<height>	<offset_center_x>	<offset_center_y>	<width>	<elevation>	<rotation>
Y_QUAD	11	411	100	100	12	50	20.0	50	0
#TREE	<s>	<t>	<w>	<h>	<offset>	<frequency>	<min h>	<max h>	<quads>	<layer>	<notes>
TREE	0	412	10	100	5	100	10	14	1	3	TREE_y_quad_offset_y
#Y_QUAD	<left>	<bottom>	<width>	<height>	<offset_center_x>	<offset_center_y>	<width>	<elevation>	<rotation>
Y_QUAD	11	411	100	100	50	25	20.0	50	0
#TREE	<s>	<t>	<w>	<h>	<offset>	<frequency>	<min h>	<max h>	<quads>	<layer>	<notes>
TREE	0	412	10	100	5	100	10	14	1	4	TREE_y_quad_offset_xy
#Y_QUAD	<left>	<bottom>	<width>	<height>	<offset_center_x>	<offset_center_y>	<width>	<elevation>	<rotation>
Y_QUAD	11	411	100	100	80	80	20.0	50	0


SKIP_SURFACE water