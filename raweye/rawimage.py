
import numpy as np
from colour_demosaicing import demosaicing_CFA_Bayer_bilinear as demosaicing
import matplotlib.pyplot as plt

def rawfAwb(rawf, rgain, bgain, bayer='rggb'):
    hrb_map = {'rggb': np.array([[rgain, 1.0],[1.0, bgain]]),
               'bggr': np.array([[bgain, 1.0],[1.0, rgain]]),
               'grbg': np.array([[1.0, rgain],[bgain, 1.0]]),
               'gbrg': np.array([[1.0, bgain],[rgain, 1.0]])}

    h_rb = hrb_map[bayer]
    b_width = rawf.shape[1]
    rawf = np.hsplit(rawf, b_width/2)
    rawf = np.vstack(rawf)
    b_shape = rawf.shape
    rawf = rawf.reshape(-1,2,2)

    rawf = rawf * h_rb

    rawf = rawf.reshape(b_shape)
    rawf = np.hstack(np.vsplit(rawf, b_width/2))
    return rawf

def raw10torawf(raw, h):
    raw10 = raw.reshape(h, -1, 5).astype(np.uint16)
    a,b,c,d,e = [raw10[...,x] for x in range(5)]
    x1 = a + ((b & 0x03) << 8)
    x2 = (b >> 2) + ((c & 0x0f) << 6)
    x3 = (c >> 4) + ((d & 0x3f) << 4)
    x4 = (d >> 6) + (e << 2)
    x1 = x1.reshape(h, -1, 1)
    x2 = x2.reshape(h, -1, 1)
    x3 = x3.reshape(h, -1, 1)
    x4 = x4.reshape(h, -1, 1)
    x = np.dstack((x1, x2, x3, x4))
    x = x.reshape(h, -1)
    return x / np.float(2**10)

def mipirawtorawf(raw, h):
    raw10 = raw.reshape(h, -1, 5).astype(np.uint16) 
    a,b,c,d,e = [raw10[...,x] for x in range(5)]
    x1 = (a << 2) + ((e >> 0) & 0x03)
    x2 = (b << 2) + ((e >> 2) & 0x03)
    x3 = (c << 2) + ((e >> 4) & 0x03)
    x4 = (d << 2) + ((e >> 6) & 0x03)
    x1 = x1.reshape(h, -1, 1)
    x2 = x2.reshape(h, -1, 1)
    x3 = x3.reshape(h, -1, 1)
    x4 = x4.reshape(h, -1, 1)
    x = np.dstack((x1, x2, x3, x4))
    x = x.reshape(h, -1)
    return x / np.float(2**10)

def raw16torawf(raw, h):
    return raw.reshape((h, -1))/np.float(2**16)

def yuv420torgb(yuv, h, isYvu=False):
    yuv = yuv.astype(np.int32)

    w = int(yuv.size / (h * 1.5))
    y = yuv[0:w*h]
    # u,v size is  h/2 * w/2
    if isYvu:
        v = yuv[w*h::2]
        u = yuv[w*h+1::2]
    else:
        u = yuv[w*h::2]
        v = yuv[w*h+1::2]

    # u,v size is  h/2 * w
    u = np.stack((u,u), axis=1).flatten()
    v = np.stack((v,v), axis=1).flatten()

    # u,v size is h * w
    u.resize(int(h/2), w)
    u = np.stack((u,u), axis=1).flatten()
    v.resize(int(h/2), w)
    v = np.stack((v,v), axis=1).flatten()

    b = 1.164 * (y-16) + 2.018 * (u - 128)
    g = 1.164 * (y-16) - 0.813 * (v - 128) - 0.391 * (u - 128)
    r = 1.164 * (y-16) + 1.596 * (v - 128)

    rgb = np.stack((r,g,b), axis=1)
    np.clip(rgb, 0, 256, out=rgb)
    rgb = rgb/256.0
    return rgb.reshape(h, w, 3)

class RawImageBase(object):
    def __init__(self, path, width, height, usize=None, offset=0, dtype=np.uint8):
        self.path = path
        self.width = width
        self.height = height
        self.usize = usize
        self.offset = offset
        self.dtype = dtype
        self.raw = None
        self.rgb = None
        pass

    def load(self):
        # 1. open file
        with open(self.path, 'rb') as infile:
            # 2. skip offset
            infile.read(self.offset)
            # 3. load date from file
            self.raw = np.fromfile(infile, self.dtype)

        # 4. force resize
        if self.width is not None and self.usize is not None:
            self.raw.resize((int(self.width * self.usize * self.height)))

        pass

    def getRGB(self):
        return self.rgb

class RawBayerImage(RawImageBase):
    def __init__(self, path, width, height, usize, offset, dtype, bayer='rggb', rawtorawf=None):
        RawImageBase.__init__(self, path=path, width=width,
                              height=height, usize=usize,
                              offset=offset, dtype=dtype)
        self.bayer = bayer
        self.rawtorawf = rawtorawf

    def load(self):
        RawImageBase.load(self)
        rawf = self.rawtorawf(self.raw, self.height)
        rawf = rawfAwb(rawf, 1.8, 1.8, self.bayer)
        self.rgb = demosaicing(rawf, self.bayer)


class Raw10Image(RawBayerImage):
    def __init__(self, path, width, height, offset=0, bayer='rggb'):
        RawBayerImage.__init__(self, path=path, width=width,
                              height=height, usize=1.25,
                              offset=offset, bayer=bayer,
                              dtype=np.uint8, rawtorawf=raw10torawf)


class MipiRawImage(RawBayerImage):
    def __init__(self, path, width, height, offset=0, bayer='rggb'):
        RawBayerImage.__init__(self, path=path, width=width,
                              height=height, usize=1.25,
                              offset=offset, bayer=bayer,
                              dtype=np.uint8, rawtorawf=mipirawtorawf)


class Raw16Image(RawBayerImage):
    def __init__(self, path, width, height, offset=0, bayer='rggb'):
        RawBayerImage.__init__(self, path=path, width=width,
                              height=height, usize=2.0,
                              offset=offset, bayer=bayer,
                              dtype=np.uint16, rawtorawf=raw16torawf)


class GrayImage(RawImageBase):
    def __init__(self, path, width, height, offset=0):
        RawImageBase.__init__(self, path=path, width=width,
                              height=height, usize=1.0,
                              offset=offset, dtype=np.uint8);

    def load(self):
        RawImageBase.load(self)
        raw = self.raw / np.float(2**8)
        self.rgb = raw.reshape(self.height, -1)


class YuvImage(RawImageBase):
    def __init__(self, path, width, height, offset=0, isYvu=False):
        RawImageBase.__init__(self, path=path, width=width,
                              height=height, usize=1.5,
                              offset=offset, dtype=np.uint8)
        self.isYvu = isYvu

    def load(self):
        RawImageBase.load(self)
        self.rgb = yuv420torgb(self.raw, self.height, self.isYvu)

class YvuImage(YuvImage):
    def __init__(self, path, width, height, offset=0):
        YuvImage.__init__(self, path=path, width=width,
                          height=height, offset=offset, isYvu=True)
