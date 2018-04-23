#ifndef CPPREFERENCE_BITS_STRINGFWD_H
#define CPPREFERENCE_BITS_STRINGFWD_H

#include <bits/memoryfwd.h>

namespace std {
template<class CharT>
class char_traits;

template <class CharT, class Traits = std::char_traits<CharT>,
          class Allocator = std::allocator<CharT> >
class basic_string;

typedef basic_string<char> string;
}  // namespace std
#endif  // CPPREFERENCE_BITS_STRINGFWD_H
