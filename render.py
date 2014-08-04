#!/usr/bin/python

from datetime import datetime, timedelta
from heightmap import HeightMap
from suncalc import solar_position
from shadowmap import ShadowMap, get_projection_north_deviation
from math import sin, cos
from os import path
from PIL import Image, ImageChops, ImageDraw
import argparse
#import tempfile
#import os

def next_time(t):
    while t <= t2:
        print t.strftime('%Y-%m-%d_%H%M.png'), '...'
        yield t

        t += delta
        print

def shadowmap_for_time(t, hm, bkg, args):
    sunpos = solar_position(t, hm.lat, hm.lng)
    dev = get_projection_north_deviation(hm.proj, hm.lat, hm.lng)
    sun_x = -sin(sunpos['azimuth'] - dev) * cos(sunpos['altitude'])
    sun_y = -cos(sunpos['azimuth'] - dev) * cos(sunpos['altitude'])
    sun_z = sin(sunpos['altitude'])

    sm = ShadowMap(hm.lat, hm.lng, hm.resolution, hm.size, hm.proj, sun_x, sun_y, sun_z, hm, 1.5)
    img = sm.to_image()
    img = img.convert('RGB')

    if bkg:
        img = Image.eval(img, lambda x: x + transparency)
        img = ImageChops.multiply(img, bkg)

    draw = ImageDraw.ImageDraw(img)
    text = t.strftime('%Y-%m-%d %H:%M')
    txtsize = draw.textsize(text)
    draw.text((hm.size - txtsize[0] - 5, hm.size - txtsize[1] - 5), text, (0,0,0))

    img.save(path.join(args.output_directory, t.strftime('%Y-%m-%d_%H%M.png')))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('heightmap', type=str, help='Path to heightmap file')
    parser.add_argument('start', type=str, help='Start date and time (YYYY-MM-DD HH:MM)')
    parser.add_argument('end', type=str, help='End date and time (YYYY-MM-DD HH:MM)')
    parser.add_argument('interval', type=int, help='Interval between images in minutes')
    parser.add_argument('output_directory', type=str, help='Path to store images in')
    parser.add_argument('--background-map', type=str, default=None, help='Path to background map image')
    parser.add_argument('--opacity', type=float, default=1, help='Opacity for shadow when overlaid (0-1)')
    parser.add_argument('--n_jobs', type=int, default=1,
            help="""Number of CPUs to use to render (defult 1) -1 means \'all
                    CPUs\'. Needs joblib""")

    args = parser.parse_args()

    if args.n_jobs != 1:
        try:
            from joblib import Parallel, delayed, load, dump
        except ImportError:
            print """If you want to use more than one CPU for rendering, you need
                     Joblib (https://pythonhosted.org/joblib/)"""
            exit()


    with open(args.heightmap, 'rb') as f:
        hm = HeightMap.load(f)

    #temp_folder = tempfile.mkdtemp()
    #filename = os.path.join(temp_folder, 'heightmap.mmap')
    #if os.path.exists(filename):
        #os.unlink(filename)
    #_ = dump(hm, filename)

    #mmap_hm = load(filename, mmap_mode='r')


    t1 = datetime.strptime(args.start, '%Y-%m-%d %H:%M')
    t2 = datetime.strptime(args.end, '%Y-%m-%d %H:%M')
    delta = timedelta(minutes=args.interval)

    bkg = None
    if args.background_map:
        bkg = Image.open(args.background_map).convert('RGB')
        transparency = int(255 - args.opacity * 255)


    if args.n_jobs != 1:
        out = Parallel(n_jobs=args.n_jobs, verbose=100)(delayed(shadowmap_for_time)(t, hm, bkg,
            args) for t in next_time(t1))
    else:
        for t in next_time(t1):
            shadowmap_for_time(t, hm, bkg, args)
