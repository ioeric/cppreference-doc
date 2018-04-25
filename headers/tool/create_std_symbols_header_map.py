#!/usr/bin/env python

"""Creates a mapping from C++ standard library symbols to their headers.

Prerequisites:
  Run clangd's global-symbol-builder with system header mapping off on
  all_in_one.cc and store the result symbols:
     $LLVM_BUILD_DIR/bin/global-symbol-builder \
--map-system-headers=false all_in_one.cc \
-- -DCPPREFERENCE_STDVER=2014 -fsyntax-only -xc++ -std=c++11 -I. \
> symbols.yaml

Usage:
  $ ./create_std_symbols_header_map.py symbols.yaml > /tmp/mapping
  $ cat /tmp/mapping
  ...
  std::vector <vector>
  std::abs <cinttypes>,<valarray>,<cmath>,<cstdlib>,<complex>
  ...
  std::string <string>
  std:: # Reduce noise

# To cross validate symbols' include headers with a mapping that is the source of truth:
  $ ./create_std_symbols_header_map.py symbols.yaml mapping > /tmp/out
"""

import argparse
import sys
import yaml

FWD_HEADER = {
    'stringfwd.h': 'string',
    'localefwd.h': 'locale',
    'memoryfwd.h': 'memory',
    'tuplefwd.h': 'tuple'
}

OVERLOADS = {
    'allocator',
    'swap',
    'copy',
    'atan',
    'tan',
    'exp',
    'cosh',
    'sinh',
    'get',
    'pow',
    'sin',
    'find',
    'sqrt',
    'fabs',
    'move',
    'atan2',
    'end',
    'getline',
    'fill',
    'copy_backward',
    'hash',
    'make_error_code',
    'make_error_condition',
    'tuple_size',
    'tuple_element',
}

# These are ambiguous symbols that we think the dummy library is not quite right
# about.
WHITE_LIST = {
    'u16streampos',  # <ios> or <iosfwd> instead of <string>
    'u32streampos',
    'wstreampos',
    'fpos', # <ios> instead of <string>
    'wclog',  # <iostream> instead of <ostream>
    'cerr',
    'clog',
    'cin',
    'wcout',
    'wcin',
    'wcerr',
    'cout',
    'basic_stream',
    'basic_iostream',
}


def main():
  if len(sys.argv) < 2:
    sys.exit('Expect at least a yaml file with index symbols. Optionally, a file, which contains'
             ' source of truth mapping with a <symbol> <header> pair on each'
             ' line, can be provided to validate symbols\' include headers in the yaml file.')
  with open(sys.argv[1], 'r') as f:
    symbols = yaml.load_all(f.read())

  source_of_truth = {}  # Source of truth mapping from symbol to header
  if len(sys.argv) == 3:
    with open(sys.argv[2], 'r') as f:
      lines = f.readlines()
      for line in lines:
        pair = line.strip().split(' ')
        source_of_truth[pair[0]] = set(pair[1].split(','))
  print >> sys.stderr, 'There are', len(source_of_truth), 'truths'
  result = {}
  for sym in symbols:
    name = sym['Name']
    if not isinstance(name, str):
      continue
    if name.startswith('operator'):
      # Ignore operator function as they can only be identified by USR.
      continue
    qualified = sym['Scope'] + name
    if not qualified.startswith('std::'):
      continue
    detail = sym.get('Detail', None)
    include_header = detail.get('IncludeHeader', None) if detail else None
    if not include_header:
      # Namespace symbols doesn't have an include
      continue

    if include_header.startswith('<'):
      inc = include_header
    else:
      paths = include_header.split('/')
      if len(paths) < 2:
        print >> sys.stderr, 'IncludeHeader too short:', include_header
        continue

      if paths[-2] == 'bits':
        include = FWD_HEADER.get(paths[-1], None)
        if include is None:
          print >> sys.stderr, 'No mapping for internal header', include_header, qualified
          continue
      else:
        include = paths[-1]
      inc = '<' + include + '>'
    if qualified not in result:
      result[qualified] = set()
    result[qualified].add(inc)
    truth = source_of_truth.get(qualified, None)
    if truth and inc not in truth:
      # These symbols have overloads that the dummy library doesn't really have.
      if name not in OVERLOADS and name not in WHITE_LIST:
        if '<iosfwd>' not in truth:  # dummy library is not good at ios symbols
          print >> sys.stderr, '%s: %s. Truth: %s.' %(qualified, inc, truth)
  sorted_result = [(k, v) for k, v in result.iteritems()]
  sorted_result.sort()
  for symbol, headers in sorted_result:
    print symbol, ','.join(headers)


if __name__ == '__main__':
  main()
