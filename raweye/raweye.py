#!/usr/bin/env python3
import sys
import argparse
import numpy as np
from colour_demosaicing import demosaicing_CFA_Bayer_bilinear as demosaicing
from colour_hdri import (
        EXAMPLES_RESOURCES_DIRECTORY,
        tonemapping_operator_simple,
        tonemapping_operator_normalisation,
        tonemapping_operator_gamma,
        tonemapping_operator_logarithmic,
        tonemapping_operator_exponential,
        tonemapping_operator_logarithmic_mapping,
        tonemapping_operator_exponentiation_mapping,
        tonemapping_operator_Schlick1994,
        tonemapping_operator_Tumblin1999,
        tonemapping_operator_Reinhard2004,
        tonemapping_operator_filmic)
import matplotlib.pyplot as plt
#from matplotlib.image import imsave
#from scipy.misc import imsave
from imageio import imwrite
from rawimage import *

g_ccm = np.array([[1.2085, -0.2502, 0.0417],
                  [-0.1174, 1.1625, -0.0452],
                  [0.0226, -0.2524, 1.2298]])

if "__main__" == __name__:
    parser = argparse.ArgumentParser(description='Show raw image or convert it to jpeg/png.',
                                    formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-H', dest='height', type=int, required=True)
    parser.add_argument('-W', dest='width', type=int)
    parser.add_argument('-s', dest='offset', type=int, default = 0)
    parser.add_argument('-t', dest='rawtype', choices = ['raw10', 'raw16', 'raw8', 'raw', 'gray', 'yuv', 'yvu'],
                        help='raw10 : continue 10bits\n'
                             'raw   : mipi 10bits\n'
                             'raw16 : 16bits\n'
                             'raw8  : 8bits\n'
                             'gray  : y 8bits\n'
                             'yuv   : yuv420 8bits\n'
                             'yvu   : yvu420 8bits')
    parser.add_argument('-b', dest='bayer', choices=['rggb', 'bggr', 'grbg', 'gbrg'], default='rggb')
    parser.add_argument('-d', dest='dgain', type=float, default=1.0, help='digit gain apply')
    parser.add_argument('-o', dest='outfile', metavar='FILE', help='write image to FILE')
    parser.add_argument('infile', metavar='InputRawFile', help='source raw image')
    args = parser.parse_args()

    if args.rawtype == None:
        args.rawtype = args.infile.split('.')[-1]

    print(args.rawtype, args.bayer, args.height, args.width, args.dgain, args.infile, args.outfile)

    rawmap = {'raw10': Raw10Image(args.infile, args.width, args.height, args.offset, args.bayer),
              'raw'  : MipiRawImage(args.infile, args.width, args.height, args.offset, args.bayer),
              'raw8': Raw8Image(args.infile, args.width, args.height, args.offset, args.bayer),
              'raw16': Raw16Image(args.infile, args.width, args.height, args.offset, args.bayer),
              'gray' : GrayImage(args.infile, args.width, args.height, args.offset),
              'yuv'  : YuvImage(args.infile, args.width, args.height, args.offset),
              'yvu'  : YvuImage(args.infile, args.width, args.height, args.offset)}

    if args.rawtype not in rawmap:
        print('unknown raw type:', args.rawtype)
        sys.exit(0)

    rawImage = rawmap[args.rawtype]
    rawImage.load()
    rgb = rawImage.getRGB()

    #rgb = np.dot(rgb, g_ccm)

    #rgb = rgb / (rgb + 1)
    #rgb = tonemapping_operator_simple(rgb)

    np.clip(rgb, 0.0, 1.0, out=rgb)

    if args.outfile:
        imwrite(args.outfile, rgb)
    else:
        plt.imshow(rgb)
        plt.show()
