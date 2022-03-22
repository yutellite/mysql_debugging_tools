python
from __future__ import print_function # python2.X support
import re

# some utilities
def std_vector_to_list(std_vector):
  """convert std::vector to list of python"""
  out_list = []
  value_reference = std_vector['_M_impl']['_M_start']
  while value_reference != std_vector['_M_impl']['_M_finish']:
    out_list.append(value_reference.dereference())
    value_reference += 1

  return out_list

def std_deque_to_list(std_deque):
  """convert std::deque to list of python"""
  out_list = []
  elttype = std_deque.type.template_argument(0)
  size = elttype.sizeof
  if size < 512:
    buffer_size = int (512 / size)
  else:
    buffer_size = 1
  
  start = std_deque['_M_impl']['_M_start']['_M_cur']
  end = std_deque['_M_impl']['_M_start']['_M_last']
  node = std_deque['_M_impl']['_M_start']['_M_node']
  last = std_deque['_M_impl']['_M_finish']['_M_cur']

  p = start
  while p != last:
    out_list.append(p.dereference())
    p += 1
    if p != end:
      continue
    node += 1
    p = node[0]
    end = p + buffer_size

  return out_list

def gdb_set_convenience_variable(var_name, var):
  """set convenience variable in python script is supported by gdb 8.0
or above, this for lower gdb version support

  """
  pass

def get_convenince_name():
  return ''

if hasattr(gdb, 'set_convenience_variable'):
  convenience_name_firstchar = 'a'
  convenience_name_sequence = [convenience_name_firstchar]

  def generate_convenince_name():
    global convenience_name_sequence
    convenience_name_maxlen = 2

    cname = ''.join(convenience_name_sequence)
    cnlen = len(convenience_name_sequence)
    for i, c in reversed(list(enumerate(convenience_name_sequence))):
      if c == 'z':
        continue
      convenience_name_sequence[i] = chr(ord(c) + 1)
      for j in range(i + 1, cnlen):
        convenience_name_sequence[j] = convenience_name_firstchar
      break
    else:
      convenience_name_sequence = [convenience_name_firstchar] * \
        (1 if cnlen == convenience_name_maxlen else (cnlen + 1))

    return cname

  def gdb_set_convenience_variable(var_name, var):
    gdb.set_convenience_variable(var_name, var)

  def get_convenince_name():
    return generate_convenince_name()

#
# threads overview/search for mysql
#

def gdb_threads():
  if hasattr(gdb, 'selected_inferior'):
    threads = gdb.selected_inferior().threads()
  else:
    threads = gdb.inferiors()[0].threads()
  return threads

def pretty_frame_name(frame_name):
  """omit some stdc++ stacks"""
  pretty_names = (
    ('std::__invoke_impl', ''),
    ('std::__invoke', ''),
    ('std::_Bind', ''),
    ('Runnable::operator()', ''),
    ('std::thread::_Invoker', ''),
    ('std::thread::_State_impl', 'std::thread'),
    ('std::this_thread::sleep_for', 'std..sleep_for'))

  for templ, val in pretty_names:
    if frame_name.startswith(templ):
      return val

  return frame_name

def brief_backtrace(filter_threads):
  frames = ''
  frame = gdb.newest_frame() if hasattr(gdb, 'newest_frame') else gdb.selected_frame()
  while frame is not None:
    frame_name = frame.name() if frame.name() is not None else '??'
    if filter_threads is not None and frame_name in filter_threads:
      return None
    frame_name = pretty_frame_name(frame_name)
    if frame_name:
      frames += frame_name + ','
    frame = frame.older()
  frames = frames[:-1]
  return frames

class ThreadSearch(gdb.Command):
  """find threads given a regex which matchs thread name, parameter name or value"""

  def __init__ (self):
    super (ThreadSearch, self).__init__ ("thread search", gdb.COMMAND_USER)

  def invoke (self, arg, from_tty):
    pattern = re.compile(arg)
    threads = gdb_threads()
    old_thread = gdb.selected_thread()
    for thr in threads:
      thr.switch()
      backtrace = gdb.execute('bt', False, True)
      matched_frames = [fr for fr in backtrace.split('\n') if pattern.search(fr) is not None]
      if matched_frames:
        print(thr.num, brief_backtrace(None))

    old_thread.switch()

ThreadSearch()

class ThreadOverview(gdb.Command):
  """print threads overview, display all frames in one line and function name only for each frame"""
  # filter Innodb backgroud workers
  filter_threads = (
    # Innodb backgroud threads
    'log_closer',
    'buf_flush_page_coordinator_thread',
    'log_writer',
    'log_flusher',
    'log_write_notifier',
    'log_flush_notifier',
    'log_checkpointer',
    'lock_wait_timeout_thread',
    'srv_error_monitor_thread',
    'srv_monitor_thread',
    'buf_resize_thread',
    'buf_dump_thread',
    'dict_stats_thread',
    'fts_optimize_thread',
    'srv_purge_coordinator_thread',
    'srv_worker_thread',
    'srv_master_thread',
    'io_handler_thread',
    'event_scheduler_thread',
    'compress_gtid_table',
    'ngs::Scheduler_dynamic::worker_proxy'
    )
  def __init__ (self):
    super (ThreadOverview, self).__init__ ("thread overview", gdb.COMMAND_USER)

  def invoke (self, arg, from_tty):
    threads = gdb_threads()
    old_thread = gdb.selected_thread()
    thr_dict = {}
    for thr in threads:
      thr.switch()
      bframes = brief_backtrace(self.filter_threads)
      if bframes is None:
        continue
      if bframes in thr_dict:
        thr_dict[bframes].append(thr.num)
      else:
        thr_dict[bframes] = [thr.num,]
    thr_ow = [(v,k) for k,v in thr_dict.items()]
    thr_ow.sort(key = lambda l:len(l[0]), reverse=True)
    for nums_thr,funcs in thr_ow:
       print(','.join([str(i) for i in nums_thr]), funcs)
    old_thread.switch()

ThreadOverview()


#
# Some convenience variables for easy debug because they are macros
#
gdb_set_convenience_variable('MAX_TABLES', gdb.parse_and_eval('sizeof(uint64_t) * 8 - 3'))
gdb_set_convenience_variable('INNER_TABLE_BIT', gdb.parse_and_eval('((uint64_t)1) << ($MAX_TABLES + 0)'))
gdb_set_convenience_variable('OUTER_REF_TABLE_BIT', gdb.parse_and_eval('((uint64_t)1) << ($MAX_TABLES + 1)'))
gdb_set_convenience_variable('RAND_TABLE_BIT', gdb.parse_and_eval('((uint64_t)1) << ($MAX_TABLES + 2)'))
gdb_set_convenience_variable('PSEUDO_TABLE_BITS', gdb.parse_and_eval('($INNER_TABLE_BIT | $OUTER_REF_TABLE_BIT | $RAND_TABLE_BIT)'))

class TreeWalker(object):
  """A base class for tree traverse"""

  def __init__(self):
    self.level_graph = []
    self.var_index = 0
    self.cname_prefix = None
    self.current_level = 0

  def reset(self):
    self.level_graph = []
    self.var_index = 0
    self.cname_prefix = get_convenince_name()

  def walk(self, expr):
    self.reset()
    type = str(expr.dynamic_type.target())
    if type == "st_select_lex_node":
      self.do_walk_select_lex_node(expr, 0)
    else:
      self.do_walk(expr, 0)
    
  def do_walk(self, expr, level):
    expr_typed = expr.dynamic_type
    expr_casted = expr.cast(expr_typed)
    self.current_level = level
    level_graph = '  '.join(self.level_graph[:level])
    for i, c in enumerate(self.level_graph):
      if c == '`':
        self.level_graph[i] = ' '
    cname = self.cname_prefix + str(self.var_index)
    left_margin = "{}${}".format('' if level == 0 else '--', cname)
    self.var_index += 1
    item_show_info = ''
    #print("step0")
    show_func = self.get_show_func(expr_typed.target())
    #print("step0.1:{},{}".format(cname, show_func))
    if show_func is not None:
      item_show_info = show_func(expr_casted)
    if item_show_info is not None:
      print("{}{} ({}) {} {}".format(
          level_graph, left_margin, expr_typed, expr, item_show_info))
    #print("step0.1:{},{}".format(cname, expr_casted))      
    gdb_set_convenience_variable(cname, expr_casted)
    #print("step1")
    walk_func = self.get_walk_func(expr_typed.target())
    #print("step2")
    if walk_func is None:
      return
    children = walk_func(expr_casted)
    #print("step3")
    if not children:
      return
    if len(self.level_graph) < level + 1:
      self.level_graph.append('|')
    else:
      self.level_graph[level] = '|'
    for i, child in enumerate(children):
      if i == len(children) - 1:
        self.level_graph[level] = '`'
      #print("step4:{},{}".format(child, child.dynamic_type))
      self.do_walk(child, level + 1)
      #print("step5")

  # SELECT_LEX/SELECT_UNIT inheit from st_select_lex_node and always 
  # use parent's pointer. so cannot use dynamic_type
  def do_walk_select_lex_node(self, expr, level):
    #top master is SELECT_UNIT.
    expr_typed=""
    expr_casted=""
    type = str(expr.dynamic_type.target())
    if type == "st_select_lex":
      expr_typed = gdb.lookup_type("st_select_lex").pointer()
      expr_casted = expr.cast(expr_typed)
    elif type == "st_select_lex_unit" or type == "st_select_lex_node":
      expr_typed = gdb.lookup_type("st_select_lex_unit").pointer()
      expr_casted = expr.cast(expr_typed)

    #print("{}, {}, {}".format(expr, expr.dynamic_type, expr_typed))
    self.current_level = level
    level_graph = '  '.join(self.level_graph[:level])
    for i, c in enumerate(self.level_graph):
      if c == '`':
        self.level_graph[i] = ' '
    cname = self.cname_prefix + str(self.var_index)
    left_margin = "{}${}".format('' if level == 0 else '--', cname)
    self.var_index += 1
    item_show_info = ''
    #print("step0")
    show_func = self.get_show_func(expr_typed.target())
    #print("step0.1:{},{}".format(cname, show_func))
    if show_func is not None:
      item_show_info = show_func(expr_casted)
    if item_show_info is not None:
      print("{}{} ({}) {} {}".format(
          level_graph, left_margin, expr_typed, expr, item_show_info))
    #print("step0.1:{},{}".format(cname, expr_casted))      
    gdb_set_convenience_variable(cname, expr_casted)
    walk_func = self.get_walk_func(expr_typed.target())
    #print("step2：{},{}".format(expr_typed.target(), walk_func))
    if walk_func is None:
      return
    children = walk_func(expr_casted)
    if not children:
      return
    if len(self.level_graph) < level + 1:
      self.level_graph.append('|')
    else:
      self.level_graph[level] = '|'
    for i, child in enumerate(children):
      if i == len(children) - 1:
        self.level_graph[level] = '`'
      self.do_walk_select_lex_node(child, level + 1)

  def get_action_func(self, item_type, action_prefix):
    def type_name(typ):
      return typ.name if hasattr(typ, 'name') else str(typ)

    func_name = action_prefix + type_name(item_type)
    #print("233{}".format(func_name))
    if hasattr(self, func_name):
      return getattr(self, func_name)

    #print("{},{}".format(func_name, item_type.fields()))
    for field in item_type.fields():
      #print("con:{}".format(field.type))
      if not field.is_base_class:
        continue
      typ = field.type
      func_name = action_prefix + type_name(typ)
      #print("final:{}".format(func_name))
      if hasattr(self, func_name):
        return getattr(self, func_name)

      return self.get_action_func(typ, action_prefix)

    return None

  def get_walk_func(self, item_type):
    return self.get_action_func(item_type, 'walk_')

  def get_show_func(self, item_type):
    return self.get_action_func(item_type, 'show_')

TreeWalker()

# Define a mysql command prefix for all mysql related command
gdb.Command('mysql', gdb.COMMAND_DATA, prefix=True)

class ItemDisplayer(object):
  """mysql item basic show functions"""
  def show_Item_ident(self, item):
    #print("1:{}".format(item))
    db_cata = []
    if item['db_name']['length']:
      #print("db_name:{}".format(item['db_name']))
      db_cata.append(item['db_name']['str'].string())
    if item['table_name']['length']:
      #print("table_name:{}".format(item['table_name']))
      db_cata.append(item['table_name']['str'].string())
    if item['field_name']['length']:
      #print("field_name:{}".format(item['field_name']))
      db_cata.append(item['field_name']['str'].string())
    #print("2:{}".format(db_cata))
    return 'field = ' + '.'.join(db_cata)

  def show_Item_int(self, item):
    return 'value = ' + str(item['value'])

  show_Item_float = show_Item_int

  def show_Item_string(self, item):
    return 'value = ' + item['str_value']['m_ptr'].string()

  def show_Item_decimal(self, item):
    sym = gdb.lookup_global_symbol('Item_decimal::val_real()')
    result = sym.value()(item)
    return 'value = ' + str(result)
    
class ExpressionTraverser(gdb.Command, TreeWalker, ItemDisplayer):
  """print mysql expression (Item) tree"""

  def __init__ (self):
    super(self.__class__, self).__init__("mysql exprtree", gdb.COMMAND_USER)

  def invoke(self, arg, from_tty):
    if not arg:
      print("usage: mysql exprtree [Item]")
      return
    expr = gdb.parse_and_eval(arg)
    self.walk(expr)

  #
  # walk and show functions for each Item class
  #

  def walk_Item_func(self, val):
    children = []
    for i in range(val['arg_count']):
      children.append(val['args'][i])
    return children

  walk_Item_sum = walk_Item_func

  def walk_Item_cond(self, val):
    end_of_list = gdb.parse_and_eval('end_of_list').address
    item_list = val['list']
    nodetype = item_list.type.template_argument(0)
    cur_elt = item_list['first']
    children = []
    while cur_elt != end_of_list:
      info = cur_elt.dereference()['info']
      children.append(info.cast(nodetype.pointer()))
      cur_elt = cur_elt.dereference()['next']
    return children

ExpressionTraverser()

def print_leaf_TABLE_LIST(leaf_tables):
    tables = ''
    has_tables = False
    i = 0
    end_of_list = gdb.parse_and_eval('end_of_list').address
    #leaf_tables = gdb.parse_and_eval(leaf_tables).address
    tl_cnname_prefix = get_convenince_name()
    list_node = leaf_tables['first']
    while list_node != end_of_list:
        has_tables = True
        table_list_typed = gdb.lookup_type("TABLE_LIST").pointer()
        table_list = list_node['info'].cast(table_list_typed).dereference()
        table_name = table_list['table_name']['str'].string()
        table_name = table_name[-18:]
        if len(table_name) == 18:
            table_name = '...' + table_name[4:]

        tl_cnname = tl_cnname_prefix + str(i)
        i += 1
        gdb_set_convenience_variable(tl_cnname, table_list)

        tables +=  '($' + tl_cnname + ')' + table_name + " " + table_list['alias']['str'].string() +  ", "
        list_node = list_node['next']

    if has_tables:
        tables = "tables: " + tables[0 : len(tables) - 2]
    else:
        tables = "no tables"
    return tables

def print_TABLE_LIST(table_list):
  tables = ''
  has_tables = False
  i = 0

  sql_i_list = table_list
  tl_cnname_prefix = get_convenince_name()
  end_of_list = gdb.parse_and_eval('end_of_list').address
  table_list = sql_i_list['first']
  while table_list and table_list.dereference():
    has_tables = True
    table_name = table_list['table_name']['str'].string()
    table_name = table_name[-18:]
    if len(table_name) == 18:
      table_name = '...' + table_name[4:]
    tl_cnname = tl_cnname_prefix +str(i)
    i += 1
    gdb_set_convenience_variable(tl_cnname, table_list)
    tables +=  '($' + tl_cnname + ')' + table_name + " " + table_list['alias']['str'].string() +  ", "
    table_list=table_list['next_local']
  if has_tables:
      tables = "tables: " + tables[0 : len(tables) - 2]
  else:
      tables = "no tables"
  return tables

def print_SELECT_LEX(select_lex):
  """print SELECT_LEX extra information"""

  table_list = select_lex['table_list']
  leaf_tables = select_lex['leaf_tables']
  return "table_list:" + print_TABLE_LIST(table_list) + "; " + "leaf_tables:" + print_leaf_TABLE_LIST(leaf_tables)

def print_SELECT_LEX_UNIT(select_lex_unit):
  try:
    return str("")
  except gdb.error:
    pass
  return ''

class QueryBlockTraverser(gdb.Command, TreeWalker):
  """print mysql query block tree"""
  def __init__ (self):
    super(self.__class__, self).__init__ ("mysql qbtree", gdb.COMMAND_USER)

  def invoke(self, arg, from_tty):
    if not arg:
      print("usage: mysql qbtree [SELECT_LEX_UNIT/SELECT_LEX]")
      return
    qb = gdb.parse_and_eval(arg)
    self.start_qb = qb.dereference()
    while qb.dereference()['master']:
      qb = qb.dereference()['master']

    self.walk(qb)

  def do_walk_query_block(self, val):
    #print("do_walk_query_block")
    cast_typed = gdb.lookup_type('st_select_lex_unit').pointer()
    blocks = []
    if not val['slave']:
      return blocks
    block = val['slave'].cast(cast_typed)
    blocks.append(block)
    while block['next']:
      block = block['next'].cast(cast_typed)
      blocks.append(block)
    return blocks
  
  def do_walk_query_unit_block(self, val):
    #print("do_walk_query_unit_block")
    cast_typed = gdb.lookup_type('st_select_lex').pointer()
    blocks = []
    if not val['slave']:
      return blocks
    block = val['slave'].cast(cast_typed)
    blocks.append(block)
    while block['next']:
      block = block['next'].cast(cast_typed)
      blocks.append(block)
    return blocks

  walk_SELECT_LEX = do_walk_query_block
  walk_st_select_lex = do_walk_query_block
  walk_st_select_lex_unit = do_walk_query_unit_block
  walk_SELECT_LEX_UNIT = do_walk_query_unit_block

  def get_current_marker(self, val):
    if self.start_qb.address != val:
      return ''
    return ' <-'
  
  def show_SELECT_LEX(self, val):
    #print("show_SELECT_LEX")
    return print_SELECT_LEX(val) + self.get_current_marker(val)

  def show_SELECT_LEX_UNIT(self, val):
    #print("show_SELECT_LEX_UNIT")
    return print_SELECT_LEX_UNIT(val) + self.get_current_marker(val)

  show_st_select_lex = show_SELECT_LEX
  show_st_select_lex_unit = show_SELECT_LEX_UNIT

QueryBlockTraverser()

class TABLE_LIST_traverser(gdb.Command):
  """print table list"""
  def __init__ (self):
    super (TABLE_LIST_traverser, self).__init__("mysql tablelist", gdb.COMMAND_USER)
  def invoke(self, arg, from_tty):
    table_list = gdb.parse_and_eval(arg).address
    print(print_TABLE_LIST(table_list))

TABLE_LIST_traverser()

class SEL_TREE_traverser(gdb.Command, TreeWalker, ItemDisplayer):
  NO_MIN_RANGE = 1
  NO_MAX_RANGE = 2
  NEAR_MIN = 4
  NEAR_MAX = 8
  """print SEL TREE"""
  def __init__ (self):
    super (self.__class__, self).__init__("mysql seltree", gdb.COMMAND_USER)

  def invoke(self, arg, from_tty):
    if not arg:
      print("usage: mysql sel_tree [SEL_TREE]")
      return
    sel_tree = gdb.parse_and_eval(arg)
    if sel_tree:
      self.walk(sel_tree)
    else:
      print('None')

  def walk_SEL_TREE(self, val):
    sel_tree_keys = val['keys']
    return self.sel_tree_keys_to_list(val)

  def show_SEL_TREE(self, val):
    sel_tree_keys = val['keys']
    sel_tree_type = val['type']
    return "[type={},keys.m_size={}]".format(sel_tree_type, sel_tree_keys['m_size'])

  def walk_SEL_ROOT(self, val):
    out_list = []
    if val:
      out_list.append(val['root'])
    return out_list

  def show_SEL_ROOT(self, val):
    if not val:
      return "None"
    sel_root_type = val['type']
    sel_root_use_count = val['use_count']
    sel_root_elements = val['elements']
    return "[type={}, use_count={}, elements={}]".format(sel_root_type, 
           sel_root_use_count, sel_root_elements);

  def walk_SEL_ARG(self, val):
    sel_arg_field = val['field']
    if not sel_arg_field:
       return None
    return self.sel_arg_tree_to_list(val)

  def show_SEL_ARG(self, val):
    sel_arg_field = val['field']
    if not sel_arg_field:
       return None

    level_graph = '  '.join(self.level_graph[:self.current_level])
    for i, c in enumerate(self.level_graph):
      if c == '`':
        self.level_graph[i] = ' '
    left_margin = "  |"

    if len(self.level_graph) < self.current_level + 1:
      self.level_graph.append('|')
    else:
      self.level_graph[self.current_level] = '|'

    field_show_info = ''
    if val['field_item']:
      field_show_info = self.get_item_show_info(val['field_item'])
      field_show_info = "{}{} field = {}".format(level_graph, left_margin,
                  field_show_info)
    
    sel_root_max_flag = val['max_flag']
    sel_root_min_flag = val['min_flag']
    left_parenthese = '['
    right_parenthese = ']'
    min_item_show_info = ''
    if val['min_item'] and self.NO_MIN_RANGE & sel_root_min_flag == 0:
      min_item_show_info = self.get_item_show_info(val['min_item'])
      if self.NEAR_MIN & sel_root_min_flag > 0:
        left_parenthese = "("
    else:
      min_item_show_info = " -infinity"
      left_parenthese = "("

    max_item_show_info = ''
    if val['max_item'] and self.NO_MAX_RANGE & sel_root_max_flag == 0:
      max_item_show_info = self.get_item_show_info(val['max_item'])
      if self.NEAR_MAX & sel_root_max_flag > 0:
        right_parenthese = ")"
    else:
      max_item_show_info = " +infinity"
      right_parenthese = ")"

    item_show_info = ''
    if sel_root_max_flag == 0 and sel_root_min_flag == 0 and val['max_item'] == val['min_item']:
      item_show_info = "{}{} equal = {}{} {}".format(level_graph, left_margin, 
                            left_parenthese, min_item_show_info, right_parenthese)
    else:
      item_show_info = "{}{} scope = {}{},{} {}".format(level_graph, left_margin,
                            left_parenthese, min_item_show_info,
                            max_item_show_info, right_parenthese)
    return "[color={}, is_asc={}, minflag={}, maxflag={}, part={}, selectivity={}]\n{}\n{}".format(
           val['color'], val['is_ascending'], sel_root_min_flag,
           sel_root_max_flag, val['part'], val['selectivity'], field_show_info, item_show_info)

  def get_item_show_info(self, expr):
    item_show_info = ''
    cname = self.cname_prefix + str(self.var_index)
    self.var_index += 1
    expr_typed = expr.dynamic_type
    expr_casted = expr.cast(expr_typed)
    item_show_info = " ${} ({}) {}".format(
             cname, expr_typed, expr)
    show_func = self.get_show_func(expr_typed.target())
    if show_func is not None:
       item_show_info = "{} {}".format(item_show_info, show_func(expr_casted))
    return item_show_info

  def sel_tree_keys_to_list(self, val):
    out_list = []
    sel_tree_keys = val['keys']
    sel_tree_keys_array = sel_tree_keys['m_array']
    for i in range(sel_tree_keys['m_size']):
      out_list.append(sel_tree_keys_array[i])
    return out_list

  def sel_arg_tree_to_list(self, val):
    out_list = []
    sel_arg_left = val['left']
    if sel_arg_left:
      out_list.append(sel_arg_left)
    sel_arg_right = val['right']
    if sel_arg_right:
      out_list.append(sel_arg_right)
    sel_arg_next_part = val['next_key_part']
    if sel_arg_next_part:
      out_list.append(sel_arg_next_part)
    return out_list

SEL_TREE_traverser()
#
# pretty printers
#

def get_value_from_list_node(nodetype, node, conname_prefix, index):
  """Returns the value held in an list_node<_Val>"""

  val = node['info'].cast(nodetype.pointer())
  val = val.cast(val.dynamic_type)

  conven_name = '%s%d' % (conname_prefix, index)
  gdb_set_convenience_variable(conven_name, val)

  return val

class PrinterIterator(object):
  """A helper class, compatiable with python 2.0"""
  def next(self):
    """For python 2"""
    return self.__next__()

class ListPrinter(object):
  """Print a MySQL List"""

  class _iterator(PrinterIterator):
    def __init__(self, nodetype, head):
      self.nodetype = nodetype
      self.base = head
      self.count = 0
      self.end_of_list = gdb.parse_and_eval('end_of_list').address
      self.convenience_name_prefix = get_convenince_name()

    def __iter__(self):
      return self

    def __next__(self):
      if self.base == self.end_of_list:
        raise StopIteration
      elt = self.base.dereference()
      self.base = elt['next']
      count = self.count
      self.count = self.count + 1
      val = get_value_from_list_node(self.nodetype, elt, self.convenience_name_prefix, count)
      return ('%s[%d]' % (self.convenience_name_prefix, count), '(%s) %s' % (val.type, val))

  def __init__(self, val):
    self.typename = val.type
    self.val = val

  def children(self):
    nodetype = self.typename.template_argument(0)
    return self._iterator(nodetype, self.val['first'])

  def to_string(self):
    return '%s' % self.typename if self.val['elements'] != 0 else 'empty %s' % self.typename

import gdb.printing
def build_pretty_printer():
  pp = gdb.printing.RegexpCollectionPrettyPrinter(
    "mysqld")
  pp.add_printer('List', '^List<.*>$', ListPrinter)
  return pp

gdb.printing.register_pretty_printer(
  gdb.current_objfile(),
  build_pretty_printer(),
  True)

# Define a mysql command prefix for all mysql related command
gdb.Command('mariadb', gdb.COMMAND_DATA, prefix=True)

"""
usage: b ha_sdb::multi_range_read_info_cost, until to `while (!seq->next(seq_it, &range))`.
       mariadb ranges &range
example: select * from t1 where a<2 or a in (3,4,5) or a>6 and a<=10 or
         a>=11 and a<15 or a>=20 and a<=30 or a>=40;
(gdb) mariadb ranges &range
"""
class SELECT_RANGES_iterator (gdb.Command):
  """Iterator the ranges in QUICK_RANGE_SEQ_CTX and print it.
  """
  def __init__ (self):
    super (SELECT_RANGES_iterator, self).__init__ ("mariadb ranges", gdb.COMMAND_USER)

  def invoke (self, args, from_tty):
    if not args:
      print("usage: mariadb ranges [&range]")
      return
    cur_range = gdb.parse_and_eval(args).dereference()
    ranges_res = gdb.parse_and_eval("seq->next(seq_it, &range)")
    while ranges_res == 0:
        cur_range = gdb.parse_and_eval("&range").dereference()
        print("{}".format(cur_range))
        ranges_res = gdb.parse_and_eval("seq->next(seq_it, &range)")
SELECT_RANGES_iterator()

"""
usage:  b handle_select
        mariadb unit select_lex->master_unit()
        mariadb unit &lex->unit
example: Q1: select * from t1,t2,t3 where t1.a = t2.a and t2.a=t3.a;
         Q2: SELECT * FROM t1 WHERE t1.a IN (SELECT a FROM t1_1 UNION  SELECT a FROM t1_2) 
             UNION SELECT * FROM t2 WHERE t2.a = (SELECT (SELECT a FROM t2_1_1 WHERE t2_1_1.a = t2_1.a) FROM t2_1 WHERE t2_1.a = t2.a) 
             UNION SELECT * FROM t3;
"""
DEBUG = 0
class SELECT_UNIT_traverser (gdb.Command):
  #help info which will show in <help user>
  #gdb)help user
  #mariadb unit -- print mariadb select_lex_unit and slave select_lex query block tree
  """print mariadb select_lex_unit and slave select_lex query block tree"""
  SELECT_LEX_START_INTVERVAL="   "
  SELECT_LEX_INHERIT_SEP = '+--'
  START_POS=""
  """mariadb unit."""
  def __init__ (self):
    super (SELECT_UNIT_traverser, self).__init__ ("mariadb unit", gdb.COMMAND_USER)

  def reset(self):
    self.SELECT_LEX_START_INTVERVAL="   "
    self.SELECT_LEX_INHERIT_SEP = '+--'
    self.START_POS=""

  def invoke (self, args, from_tty):
    if not args:
      print("usage: mariadb unit [SELCT UNIT]")
      return
    #reset the format string
    self.reset()
    #arg0 should be the SELECT_UNIT  
    select_unit=gdb.parse_and_eval(args)
    if not select_unit:
      print('None')
      return
   
    #print ("SELECT_LEX_UNIT is:{}".format(select_unit))
    self.print_unit(select_unit)

  #print table list
  def print_table_list(self, table_list, start_pos):
    if not table_list:
      if DEBUG:
        print("print table_list has no inpurt table_list.")
      return
    table_cnt = table_list['elements']
    table_pos = 0
    k = 0
    table = table_list['first']
    if table_cnt == 1:
        #print with new line
        print("{}table:{}".format(start_pos, table['table_name']['str']))
    else:
        #print without new line, with sep of ','
        print("{}table:{}".format(start_pos, table['table_name']['str']), end=', ')
    for k in range(1, table_cnt):
        table = table['next_local']
        if k < table_cnt - 1:
            print("table:{}".format(table['table_name']['str']), end=', ')
        else:
            print("table:{}".format(table['table_name']['str']), end='\n')

  def print_select_lex(self, select_lex):
    prefix_print_string = ""
    i = 0
    if not select_lex:
      if DEBUG:
        print("print select has no inpurt lex.")
      return

    prefix_print_string = self.START_POS + self.SELECT_LEX_INHERIT_SEP
    print("{}SELECT_LEX: this:{}, next:{}, prev:{}, master:{}, slave:{}, link_next:{}, link_prev:{}".\
      format(prefix_print_string, select_lex, \
      select_lex['next'], select_lex['prev'], select_lex['master'], \
      select_lex['slave'], select_lex['link_next'], select_lex['link_prev']))

    #cast the st_select_lex_node* to st_select_lex*
    #print the where expression and table list.
    select_lex_obj = select_lex.cast(gdb.lookup_type('st_select_lex').pointer())
    cnt_of_spaces = len(prefix_print_string + "SELECT_LEX: ")
    k=0
    print_pos_of_table_list=""
    for k in range(0, cnt_of_spaces): 
        print_pos_of_table_list=print_pos_of_table_list+" "
    #table list
    table_list=select_lex_obj['table_list']
    self.print_table_list(table_list, print_pos_of_table_list)
    print("{}where:{}".format(print_pos_of_table_list, select_lex_obj['where']))

    #select_lex_obj['table_list'], 

    #print the slave select_unit
    if select_lex['slave']:
        self.START_POS = self.START_POS + self.SELECT_LEX_START_INTVERVAL
        select_unit=select_lex['slave']
        self.print_unit(select_unit)
        #remove "   " from end of 
        self.START_POS = self.START_POS[:-3]

    #print the nerbor next select_lex
    self.print_select_lex(select_lex['next'])

  def print_unit(self, select_unit):
    prefix_print_string = ""
    i = 0
    if not select_unit:
      print("print unit has no inpurt unit.")
      return

    prefix_print_string = self.START_POS + self.SELECT_LEX_INHERIT_SEP
    print("{}SELECT_UNIT:   this:{}, next:{}, prev:{}, master:{}, slave:{}, link_next:{}, link_prev:{}".\
      format(prefix_print_string, select_unit, select_unit['next'],\
      select_unit['prev'], select_unit['master'], select_unit['slave'], \
      select_unit['link_next'], select_unit['link_prev']))
    if select_unit['slave']:
      self.START_POS = self.START_POS + self.SELECT_LEX_START_INTVERVAL
      select_lex=select_unit['slave']
      #print the slave select_lex
      self.print_select_lex(select_lex)#remove "   " from end of 
      self.START_POS = self.START_POS[:-3]
SELECT_UNIT_traverser()

"""
usage:  mariadb dtype select_lex->having
example: Q1: select * from t1 having a > 1+2;
"""
class DYNAMIC_TYPE (gdb.Command):
  """print the dynamic type."""
  def __init__(self):
    super(DYNAMIC_TYPE, self).__init__("mariadb dtype", gdb.COMMAND_USER)

  def invoke (self, args, from_tty):
    if not args:
      print("usage: mariadb dtype [item]")
      return
    #convert the argument to string literal value for gdb.parse_and_eval(expr).
    expr=str(args)
    print("({}){}".format(str(gdb.parse_and_eval(expr).dynamic_type), \
      gdb.parse_and_eval(args).dereference().address))
DYNAMIC_TYPE()


class SELECT_CONDITION (gdb.Command):
  #Print the expression such as where, having, order by..b.
  def __init__ (self):
    super (SELECT_CONDITION, self).__init__ ("mariadb condition", gdb.COMMAND_USER)

  def invoke (self, args, from_tty):
    if not args:
      print("usage: mariadb condition [where]")
      return
    #convert the argument to string literal value for gdb.parse_and_eval(expr).
    expr=str(args)
    actual_cond = gdb.parse_and_eval(expr).cast(gdb.parse_and_eval(expr).dynamic_type)

    #The following is call a function of gdb.value()
    cond_cast_string = str(gdb.parse_and_eval(expr).dynamic_type)
    cond_addr_string = str(gdb.parse_and_eval(expr).dereference().address)
    print("{}".format("step1"))
    actual_cond_expr = '((%s)%s)' % (cond_cast_string, cond_addr_string)
    #0x7f9ca4016288
    #mariadb condition select_lex->having
    #0x7f9ca4016288, (Item_func_gt *)0x7f9ca4016288
    #print("{}, {}".format(actual_cond, actual_cond_expr))
    call_type_string = '%s->type()' % (actual_cond_expr)
    call_functype_string = '%s->functype()' % (actual_cond_expr)
    #((Item_func_gt *)0x7f9ca4016288)->type(), Item::FUNC_ITEM
    print("{}, {}".format(call_type_string, gdb.parse_and_eval(call_type_string)))
    #((Item_func_gt *)0x7f9ca4016288)->functype(), Item_func::GT_FUNC
    print("{}, {}".format(call_functype_string, gdb.parse_and_eval(call_functype_string)))

    Item_type = str(gdb.parse_and_eval(call_type_string))
    if Item_type == "Item::FUNC_ITEM":
      print("this is Item::func")
SELECT_CONDITION()
end
