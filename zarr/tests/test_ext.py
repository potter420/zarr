# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, division


from nose.tools import eq_ as eq, assert_raises
import numpy as np
import zarr
from zarr.ext import get_cparams


def test_get_cparams():

    # defaults
    cname, clevel, shuffle = get_cparams()
    eq(zarr.defaults.cname, cname)
    eq(zarr.defaults.clevel, clevel)
    eq(zarr.defaults.shuffle, shuffle)

    # valid
    cname, clevel, shuffle = get_cparams('zlib', 1, 2)
    eq(b'zlib', cname)
    eq(1, clevel)
    eq(2, shuffle)

    # bad cname
    with assert_raises(ValueError):
        get_cparams('foo', 1, True)

    # bad clevel
    with assert_raises(ValueError):
        get_cparams('zlib', 11, True)

    # bad shuffle
    with assert_raises(ValueError):
        get_cparams('zlib', 1, 3)


def _test_create_chunk_default(a):
    c = zarr.Chunk(a.shape, a.dtype)
    c[:] = a

    # check properties
    eq(a.shape, c.shape)
    eq(a.dtype, c.dtype)
    eq(a.nbytes, c.nbytes)
    eq(zarr.defaults.cname, c.cname)
    eq(zarr.defaults.clevel, c.clevel)
    eq(zarr.defaults.shuffle, c.shuffle)

    # check compression is sane
    assert c.cbytes < c.nbytes
    assert c.blocksize <= c.nbytes

    # check round-trip
    assert np.array_equal(a, c[:])


def _test_create_chunk_cparams(a, cname, clevel, shuffle):
    c = zarr.Chunk(a.shape, a.dtype, cname, clevel, shuffle)
    c[:] = a

    # check properties
    eq(a.shape, c.shape)
    eq(a.dtype, c.dtype)
    eq(a.nbytes, c.nbytes)
    eq(cname, c.cname)
    eq(clevel, c.clevel)
    eq(shuffle, c.shuffle)

    # check compression is sane
    assert c.blocksize <= c.nbytes
    if clevel > 0 and shuffle > 0:
        # N.B., for some arrays, shuffle is required to achieve any compression
        assert c.cbytes < c.nbytes, (c.nbytes, c.cbytes)

    # check round-trip
    assert np.array_equal(a, c[:])


def _test_create_chunk(a):
    _test_create_chunk_default(a)
    for cname in b'blosclz', b'lz4', b'snappy', b'zlib':
        for clevel in 0, 1, 5, 9:
            for shuffle in 0, 1, 2:
                print(cname, clevel, shuffle)
                _test_create_chunk_cparams(a, cname, clevel, shuffle)


def test_create_chunk():

    # arange
    for dtype in 'u1', 'u4', 'u8', 'i1', 'i4', 'i8':
        print(dtype)
        print('1-dimensional')
        _test_create_chunk(np.arange(1e5, dtype=dtype))
        print('2-dimensional')
        _test_create_chunk(np.arange(1e5, dtype=dtype).reshape((100, -1)))

    # linspace
    for dtype in 'f2', 'f4', 'f8':
        print(dtype)
        print('1-dimensional')
        _test_create_chunk(np.linspace(-1, 1, 1e5, dtype=dtype))
        print('2-dimensional')
        _test_create_chunk(np.linspace(-1, 1, 1e5, dtype=dtype).reshape((100, -1)))


def test_create_chunk_fill_value():

    shape = 100,

    # default dtype and fill_value
    c = zarr.Chunk(shape)
    a = c[:]
    eq(shape, a.shape)
    eq(np.dtype(None), a.dtype)

    # specified dtype and fill_value
    dtype = 'u4'
    fill_value = 1
    c = zarr.Chunk(shape, dtype=dtype, fill_value=fill_value)
    a = c[:]
    e = np.empty(shape, dtype=dtype)
    e.fill(fill_value)
    assert np.array_equal(e, a)