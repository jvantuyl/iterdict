#!/usr/bin/env python

# Copyright (c) 2012, Kirk Strauser <kirk@strauser.com>
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
#   Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""Define a IterDict class which lazily evaluates initialization objects passed
into it"""

__all__ = ['IterDict']

from functools import wraps

@wraps(wraps)
def wraps(wrapped):
    from functools import wraps, WRAPPER_ASSIGNMENTS
    wr_ass = set(WRAPPER_ASSIGNMENTS)
    wr_ass.remove('__module__')
    return wraps(wrapped, wr_ass)

def slurpfirst(f):
    @wraps(f)
    def func(self, *args, **kwargs):
        self.slurp()
        return f(self, *args, **kwargs)
    return func

NONE = object()

class IterDict(dict):
    """IterDicts are dicts at heart and behave almost identically, with the
    exception that they can be initialized with large or infinite iterators and
    use lazy evaluation to avoid resolving keys until those keys are actually
    referenced. As new items from the iterator are processed, they are added
    into the dict as usually.

    Note: since iterator processing is deferred as long as possible, it respects
    keys that have been already added to or deleted from the dict. That is,
    it won't overwrite a key present in the dict, and it won't create a key if
    that key has already been deleted from the dict. Surprises are bad."""

    @wraps(dict.__init__)
    def __init__(self, *args, **kwargs):
        super(IterDict, self).__init__()
        self.__iterator = None
        if args:
            assert len(args) == 1, 'too many arguments'
            self.__iterator = args[0]
        self.update(**kwargs)

    def slurp(self, target=NONE):
        """consumes values from the iterator until it's all gone"""
        if self.__iterator is None:
            self.clean()
            return True
        if target in self:
            break
        for k,v in self.__iterator:
            self[k] = v
            if k == target:
                return True
        self.clean()
        return False

    @wraps(dict.iteritems)
    def iteritems(self, *args, **kwargs):
        for k,v in super(IterDict, self).iteritem():
            yield k
        if not self.__iterator is None:
            for k,v in self.__iterator:
                self[k] = v
                yield k

    @wraps(dict.iterkeys)
    def iterkeys(self, *args, **kwargs):
        for k,v in self.iteritems():
            yield k

    @wraps(dict.itervalues)
    def itervalues(self, *args, **kwargs):
        for k,v in self.iteritems():
            yield v

    @wraps(dict.__contains__)
    def __contains__(self, key):
       return self.slurp(key)

    pop = slurpfirst(dict.pop)
    __getitem__ = slurpfirst(dict.__getitem__)
    __delitem__ = slurpfirst(dict.__delitem__)

    def clean(self):
        """makes this into a normal dict after we're done"""
        del self.slurp
        del self.clean
        clean = super(IterDict, self)
        self.__iterator = None
        self.__getitem__ = clean.__getitem__
        self.__delitem__ = clean.__delitem__
        self.__contains__ = clean.__contains__
        self.iteritems = clean.iteritems
        self.iterkeys = clean.iterkeys
        self.itervalues = clean.itervalues
        self.pop = clean.pop
        self.__repr__ = clean.__repr__

    def __repr__(self):
        return 'IterDict<%s, fed by %s>' % (
            super(IterDict, self).__repr__(),
            repr(self.__iterator)
        )

