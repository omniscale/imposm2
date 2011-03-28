# Copyright 2011 Omniscale (http://omniscale.com)
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import difflib

def merge(a, b):
    sqm = difflib.SequenceMatcher(None, a, b)
    matching_blocks = sqm.get_matching_blocks()
    matching_blocks.pop(-1)
    
    if not matching_blocks:
        return None
    
    a_idx = b_idx = 0
    result = []

    for block in matching_blocks:
        if a_idx < block[0]:
            result.extend(a[a_idx:block[0]])
        if b_idx < block[1]:
            result.extend(b[b_idx:block[1]])
        a_idx = block[0]+block[-1]
        b_idx = block[1]+block[-1]
        result.extend(a[block[0]:block[0]+block[-1]])

    if a_idx < len(a):
        result.extend(a[a_idx:])
    if b_idx < len(b):
        result.extend(b[b_idx:])
        
    return result


def multimerge(candidates, merge_func=merge):
    candidates = list(candidates)
    while len(candidates) > 1:
        a, b, res = multimerge_(candidates, merge_func)
        if res is None:
            return candidates
        candidates.remove(b)
        if a is not res:
            candidates.remove(a)
            candidates.append(res)
        # else: in place merge
    return candidates[0]

def multimerge_(candidates, merge_func):
    for a, b in permutations(candidates, 2):
        res = merge_func(a, b)
        if res is not None:
            return a, b, res
    return None, None, None


try:
    from itertools import permutations
    permutations # prevent warning
except ImportError:
    def permutations(iterable, r=None):
        # permutations('ABCD', 2) --> AB AC AD BA BC BD CA CB CD DA DB DC
        # permutations(range(3)) --> 012 021 102 120 201 210
        pool = tuple(iterable)
        n = len(pool)
        r = n if r is None else r
        if r > n:
            return
        indices = range(n)
        cycles = range(n, n-r, -1)
        yield tuple(pool[i] for i in indices[:r])
        while n:
            for i in reversed(range(r)):
                cycles[i] -= 1
                if cycles[i] == 0:
                    indices[i:] = indices[i+1:] + indices[i:i+1]
                    cycles[i] = n - i
                else:
                    j = cycles[i]
                    indices[i], indices[-j] = indices[-j], indices[i]
                    yield tuple(pool[i] for i in indices[:r])
                    break
            else:
                return