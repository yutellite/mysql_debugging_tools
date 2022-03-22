
#mariadb condition select_lex->having

"""
  thread search
  thread overview
  mysql exprtree => ok for mariadb
  mysql qbtree
  mysql tl
  mysql sel_tree
  mariadb ranges
  mariadb unit
  mariadb dtype
  mariadb condition
"""

"""
(gdb) mariadb ranges &range
{start_key = {key = 0x7fa06c09cb68 "\001", length = 5, keypart_map = 1, flag = HA_READ_AFTER_KEY}, end_key = {key = 0x7fa06c09cb70 "", length = 5, keypart_map = 1, flag = HA_READ_BEFORE_KEY}, ptr = 0x0, range_flag = 0}
{start_key = {key = 0x7fa06c09cb68 "", length = 5, keypart_map = 1, flag = HA_READ_KEY_EXACT}, end_key = {key = 0x7fa06c09cb70 "", length = 5, keypart_map = 1, flag = HA_READ_AFTER_KEY}, ptr = 0x0, range_flag = 32}
{start_key = {key = 0x7fa06c09cb68 "", length = 5, keypart_map = 1, flag = HA_READ_KEY_EXACT}, end_key = {key = 0x7fa06c09cb70 "", length = 5, keypart_map = 1, flag = HA_READ_AFTER_KEY}, ptr = 0x0, range_flag = 32}
{start_key = {key = 0x7fa06c09cb68 "", length = 5, keypart_map = 1, flag = HA_READ_KEY_EXACT}, end_key = {key = 0x7fa06c09cb70 "", length = 5, keypart_map = 1, flag = HA_READ_AFTER_KEY}, ptr = 0x0, range_flag = 32}
{start_key = {key = 0x7fa06c09cb68 "", length = 5, keypart_map = 1, flag = HA_READ_AFTER_KEY}, end_key = {key = 0x7fa06c09cb70 "", length = 5, keypart_map = 1, flag = HA_READ_AFTER_KEY}, ptr = 0x0, range_flag = 0}
{start_key = {key = 0x7fa06c09cb68 "", length = 5, keypart_map = 1, flag = HA_READ_KEY_EXACT}, end_key = {key = 0x7fa06c09cb70 "", length = 5, keypart_map = 1, flag = HA_READ_BEFORE_KEY}, ptr = 0x0, range_flag = 0}
{start_key = {key = 0x7fa06c09cb68 "", length = 5, keypart_map = 1, flag = HA_READ_KEY_EXACT}, end_key = {key = 0x7fa06c09cb70 "", length = 5, keypart_map = 1, flag = HA_READ_AFTER_KEY}, ptr = 0x0, range_flag = 0}
{start_key = {key = 0x7fa06c09cb68 "", length = 5, keypart_map = 1, flag = HA_READ_KEY_EXACT}, end_key = {key = 0x7fa06c09cb70 "", length = 0, keypart_map = 0, flag = HA_READ_AFTER_KEY}, ptr = 0x0, range_flag = 0}
"""

##2
"""
(gdb) mariadb unit &lex->unit
+--SELECT_UNIT:   this:0x7fa06c004f38, next:0x0, prev:0x0, master:0x0, slave:0x7fa06c015278, link_next:0x0, link_prev:0x0
   +--SELECT_LEX: this:0x7fa06c015278, next:0x0, prev:0x7fa06c004f50, master:0x7fa06c004f38, slave:0x0, link_next:0x0, link_prev:0x7fa06c005bc8
                  table:0x7fa06c015850 "t1", table:0x7fa06c015f78 "t2", table:0x7fa06c0166a0 "t3"
                  where:0x7fa06c017798
(gdb) mariadb unit select_lex->master_unit()
+--SELECT_UNIT:   this:0x7fa06c004f38, next:0x0, prev:0x0, master:0x0, slave:0x7fa06c015418, link_next:0x0, link_prev:0x0
   +--SELECT_LEX: this:0x7fa06c015418, next:0x7fa06c0193c0, prev:0x7fa06c004f50, master:0x7fa06c004f38, slave:0x7fa06c016f80, link_next:0x0, link_prev:0x7fa06c016288
                  table:0x7fa06c0159f0 "t1"
                  where:0x7fa06c018920
      +--SELECT_UNIT:   this:0x7fa06c016f80, next:0x0, prev:0x7fa06c015430, master:0x7fa06c015418, slave:0x7fa06c016268, link_next:0x0, link_prev:0x0
         +--SELECT_LEX: this:0x7fa06c016268, next:0x7fa06c017790, prev:0x7fa06c016f98, master:0x7fa06c016f80, slave:0x0, link_next:0x7fa06c015418, link_prev:0x7fa06c0177b0
                        table:0x7fa06c016848 "t1_1"
                        where:0x0
         +--SELECT_LEX: this:0x7fa06c017790, next:0x0, prev:0x7fa06c016268, master:0x7fa06c016f80, slave:0x0, link_next:0x7fa06c016268, link_prev:0x7fa06c0193e0
                        table:0x7fa06c017d70 "t1_2"
                        where:0x0
   +--SELECT_LEX: this:0x7fa06c0193c0, next:0x7fa06c09f9b8, prev:0x7fa06c015418, master:0x7fa06c004f38, slave:0x7fa06c09e8f0, link_next:0x7fa06c017790, link_prev:0x7fa06c01a230
                  table:0x7fa06c019998 "t2"
                  where:0x7fa06c09f2e8
      +--SELECT_UNIT:   this:0x7fa06c09e8f0, next:0x0, prev:0x7fa06c0193d8, master:0x7fa06c0193c0, slave:0x7fa06c01a210, link_next:0x0, link_prev:0x0
         +--SELECT_LEX: this:0x7fa06c01a210, next:0x0, prev:0x7fa06c09e908, master:0x7fa06c09e8f0, slave:0x7fa06c09d228, link_next:0x7fa06c0193c0, link_prev:0x7fa06c01a6b8
                        table:0x7fa06c09dcd0 "t2_1"
                        where:0x7fa06c09e698
            +--SELECT_UNIT:   this:0x7fa06c09d228, next:0x0, prev:0x7fa06c01a228, master:0x7fa06c01a210, slave:0x7fa06c01a698, link_next:0x0, link_prev:0x0
               +--SELECT_LEX: this:0x7fa06c01a698, next:0x0, prev:0x7fa06c09d240, master:0x7fa06c09d228, slave:0x0, link_next:0x7fa06c01a210, link_prev:0x7fa06c09f9d8
                              table:0x7fa06c01ac78 "t2_1_1"
                              where:0x7fa06c01af68
   +--SELECT_LEX: this:0x7fa06c09f9b8, next:0x0, prev:0x7fa06c0193c0, master:0x7fa06c004f38, slave:0x0, link_next:0x7fa06c01a698, link_prev:0x7fa06c005bc8
                  table:0x7fa06c09ff90 "t3"
                  where:0x0
"""

##3
"""
(gdb) p select_lex->having
$9 = (Item *) 0x7f9ca4016288
(gdb) mariadb dtype select_lex->having
(Item_func_gt *)0x7f9ca4015308
"""

##4
"""
mysql tablelist select_lex->table_list
python print("{}".format(gdb.parse_and_eval("select_lex->table_list").type))
python print("{}".format(gdb.parse_and_eval("select_lex->table_list.next")))
(gdb) mysql tablelist select_lex->table_list
tables: ($c0)t1 t1
"""


```sql
SELECT *
FROM t1
WHERE t1.a IN (
    SELECT a
    FROM t1_1
    
    UNION
    
    SELECT a
    FROM t1_2
    )

UNION

SELECT *
FROM t2
WHERE t2.a = (
    SELECT (
        SELECT a
        FROM t2_1_1
        WHERE t2_1_1.a = t2_1.a
        )
    FROM t2_1
    WHERE t2_1.a = t2.a
    )

UNION

SELECT *
FROM t3;
```
##5 
"""
mysql qbtree select_lex
(gdb) mysql qbtree select_lex
$a0 (st_select_lex_unit *) 0x7f8978004f38
|--$a1 (st_select_lex *) 0x7f8978015480
|  `--$a2 (st_select_lex_unit *) 0x7f8978016fe8
|     |--$a3 (st_select_lex *) 0x7f89780162d0
|     `--$a4 (st_select_lex *) 0x7f89780177f8
|--$a5 (st_select_lex *) 0x7f8978019428
|  `--$a6 (st_select_lex_unit *) 0x7f8978058bd8
|     `--$a7 (st_select_lex *) 0x7f897801a278
|        `--$a8 (st_select_lex_unit *) 0x7f8978057670
|           `--$a9 (st_select_lex *) 0x7f897801a700
`--$a10 (st_select_lex *) 0x7f8978059ca0
"""

##6
"""
mysql exprtree select_lex->having
(gdb) mysql exprtree select_lex->having
$a0 (Item_cond_and *) 0x7f8978016a68
|--$a1 (Item_func_gt *) 0x7f89780162a0
|  |--$a2 (Item_ref *) 0x7f8978015f68 field = a
|  `--$a3 (Item_func_plus *) 0x7f89780161d0
|     |--$a4 (Item_int *) 0x7f8978016098 value = 1
|     `--$a5 (Item_int *) 0x7f8978016138 value = 2
`--$a6 (Item_func_gt *) 0x7f8978016828
   |--$a7 (Item_ref *) 0x7f89780164e8 field = c
   `--$a8 (Item_func_minus *) 0x7f8978016750
      |--$a9 (Item_int *) 0x7f8978016618 value = 6
      `--$a10 (Item_int *) 0x7f89780166b8 value = 1
"""