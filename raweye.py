#!/usr/bin/env python3
import sys
import argparse
import numpy as np
from colour_demosaicing import demosaicing_CFA_Bayer_bilinear as demosaicing
import matplotlib.pyplot as plt
#from matplotlib.image import imsave
from scipy.misc import imsave

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

def raw16torawf(raw, h):
    return raw.reshape((h, -1))/np.float(2**16)

if "__main__" == __name__:
    parser = argparse.ArgumentParser(description='Show raw image or convert it to jpeg/png.')
    parser.add_argument('-H', dest='height', type=int, required=True)
    parser.add_argument('-W', dest='width', type=int)
    parser.add_argument('-t', dest='rawtype', choices = ['raw10', 'raw16', 'raw'],
                        help='raw10: continue 10bits, raw: mipi 10bits, raw16: 16bits')
    parser.add_argument('-b', dest='bayer', choices=['rggb', 'bggr', 'grbg', 'gbrg'], default='rggb')
    parser.add_argument('-d', dest='dgain', type=float, default=1.0, help='digit gain apply')
    parser.add_argument('-o', dest='outfile', metavar='FILE', help='write image to FILE')
    parser.add_argument('infile', metavar='InputRawFile', help='source raw image')
    args = parser.parse_args()

    if args.rawtype == None:
        args.rawtype = args.infile.split('.')[1]

    print(args.rawtype, args.bayer, args.height, args.dgain, args.infile, args.outfile)

    rawmap = {'raw10': (np.uint8,  raw10torawf),
              'raw'  : (np.uint8,  mipirawtorawf),
              'raw16': (np.uint16, raw16torawf)}

    if args.rawtype not in rawmap:
        print('unknown raw type:', args.rawtype)
        sys.exit(0)

    dataType, rawtorawf = rawmap[args.rawtype]

    raw = np.fromfile(args.infile, dataType)
    if args.width != None:
        raw.resize((int(args.width * 1.25 * args.height)))

    rawf = rawtorawf(raw, args.height)
    print('raw image shape:', rawf.shape)

    if args.dgain > 1.0:
        rawf = rawf * args.dgain
    np.clip(rawf, 0.0, 1.0, out=rawf)

    rgb = demosaicing(rawf, args.bayer)

    if args.outfile:
        imsave(args.outfile, rgb) 
    else:
        plt.imshow(rgb)
        plt.show()
