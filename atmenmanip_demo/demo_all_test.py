#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 19 12:14:35 2018

@author: postla
"""

# python standard classes
import numpy as np
from matplotlib import pyplot as plt
from scipy import ndimage
import cv2 # for noise filters
import imp

# specific application classes
from pathfindlib import pfl_interface as pf
from imgrecoglib import irl_interface as ir

plt.close("all")

## Demo
# Image recognition
arr_sigma = (7, 8)
arr_noisetol = (5e-5, 5e-4)
#arr_picobj = []
#for k in range(2):
#    folder = "_image_recognition/pics"
#    filename = "GonQF_{:02d}".format(k+5) + ".npy"
#    pic = np.load(folder + "/" + filename)
#    sigma = arr_sigma[k]
#    noisetol = arr_noisetol[k]
#
#    arr_picobj.append( ir.Picture(pic, filename, sigma, noisetol) )
#    arr_picobj[-1].blur_image()
#    arr_picobj[-1].detect_maxima()
#    arr_picobj[-1]._plot()

for k in range(1, 2):
    folder = "."
    filename = "GonQF_{:02d}".format(k+1) + ".npy"
    pic = np.load(folder + "/" + filename)
    sigma = arr_sigma[k]
    noisetol = arr_noisetol[k]

    picobj = ir.Picture(pic, filename, sigma, noisetol)
    picobj.blur_image()
    picobj.detect_maxima()
    picobj._plot()

# Sites and bonds
sites = []
maxima = picobj.maxima[0]
max_bond_length = 55 # in nm
for m in maxima:
    sites.append(pf.Site(m[0], m[1], max_bond_radius = max_bond_length))

bonds = pf.Bonds(sites, max_bond_length)

# Path finding
N_sites = len(sites)
N_foreign = 5

invalid_config = True
while invalid_config:
    idx_sites_sources = np.random.randint(N_sites, size = N_foreign)
    idx_sites_targets = np.random.randint(N_sites, size = N_foreign)

    sources = np.array([])
    targets = np.array([])

    for i in range(len(idx_sites_sources)):
        sources = np.append(sources, pf.Atom(sites[idx_sites_sources[i]], "Si") )
        targets = np.append(targets, sites[idx_sites_targets[i]] )

    try:
        MyPathlist = pf.MultiplePaths_NoOverlap(sources, targets)
    except ValueError:
        continue 
    else:
        MyPathlist.determine_paths()
        invalid_config = False

### Plotting and that
colors = ("gray", "blue", "green", "cyan", "orange")

# Plot crystal
plt.figure()#, figsize = (5, 5), dpi = 100)
plt.gca().invert_yaxis()

plotx = []
ploty = []
for k in range(len(sites)):
    plotx.append(sites[k].coords[1])
    ploty.append(sites[k].coords[0])
plt.plot(plotx, ploty, 'kx')
plt.axis('equal')

# Plot bonds
for k in range(len(bonds.members)):
    plotx = (bonds.members[k].coords()[0][1], bonds.members[k].coords()[1][1])
    ploty = (bonds.members[k].coords()[0][0], bonds.members[k].coords()[1][0])
    p = plt.plot(plotx, ploty, color = "red", linestyle = "dotted", alpha = 0.4)
    
# Plot sources
plotx = []
ploty = []
for i in range(len(sources)):
    plotx = (MyPathlist.atoms[i].orig.coords[1])
    ploty = (MyPathlist.atoms[i].orig.coords[0])
    p = plt.plot(plotx, ploty, 'o', mfc="none")[0]
    p.set_markerfacecolor(colors[i%len(colors)])
    p.set_markersize(10)

# Plot targets / sinks
plotx = []
ploty = []
for i in range(len(sources)):
    plotx = (MyPathlist.sites_target[i].coords[1])
    ploty = (MyPathlist.sites_target[i].coords[0])
    p = plt.plot(plotx, ploty, 'bo', alpha = 0.5)[0]
    p.set_markerfacecolor("1")
    p.set_markeredgecolor(colors[i%len(colors)])
    p.set_markersize(20)

# Plot path
linestyles = ("dotted", "dashed", "solid")
appearances = np.meshgrid(colors, linestyles)
for i in range(len(MyPathlist.members)):
    plotx = []
    ploty = []
    testpath = MyPathlist.members[i]
    for k in range(len(testpath.sitelist)):
        plotx.append(testpath.sitelist[k].coords[1])
        ploty.append(testpath.sitelist[k].coords[0])
    p = plt.plot(plotx, ploty, label = "Path %d" % i)[0]
    # p.set_color("%s" % (1 - i/len(sources)))
    p.set_linestyle(appearances[1].flat[i%len(appearances[1].flat)])
    p.set_color(appearances[0].flat[i%len(appearances[0].flat)])
    p.set_linewidth(2)

plt.legend()
plt.show()
