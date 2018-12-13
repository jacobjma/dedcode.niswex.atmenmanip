#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug  3 15:14:25 2018

@author: postla
"""
# hardware classes
from keithley_multimeter import keithley2000
# specific application classes
try:
    from pathfindlib import pfl_interface as oopf
    from pathfindlib import create_crystal as cc
except:
    import pfl_interface as oopf
    import create_crystal as cc
# python standard classes
import numpy as np
from matplotlib import pyplot as plt
import logging
import time

#TODO: rewrite code to OOP
sim_mode = True
try:
    keithley = keithley2000.KEITHLEY2000()
    logging.info("Connected to feedback-responding device")
except:
    keithley = None
    logging.info("Something went wrong! Error #001")

def AM(paths, api, document_controller):
    if not keithley:
        return
        logging.info("No feedback-responding device")
    # init
    superscan = None
    if sim_mode:
        hwsrc = "usim_scan_device"
    else:
        hwsrc = "scan_controller"
    superscan = api.get_hardware_source_by_id(hwsrc, "1")

    # auxiliary function
    def runmap(stop_event, frametimeout, jump_threshold=0.15, drift_threshold=0.1):
        frame_number = 1
        while not stop_event.wait(0.1):
            xdata_list = superscan.record()
            for xdata in xdata_list:
                data_item = None
                def create_data_item():
                    nonlocal data_item
                    data_item = document_controller.create_data_item_from_data_and_metadata(xdata)
                api.queue_task(create_data_item)
                starttime = time.time()
                while data_item is None and not time.time() - starttime > 3: # only wait 3s maximum for data item to appear
                    time.sleep(0.2)
                metadata_dict = data_item.metadata
                metadata_dict.setdefault('Auto-Manipulator', dict())['frame_number'] = frame_number
                #metadata_dict.setdefault('Auto-Manipulator', dict())['tractor_time'] = frametimeout
                #metadata_dict.setdefault('Auto-Manipulator', dict())['autodetect_jumps'] = autodetect_checked

                pp_dem_xy = current_sitelist[current_position_in_sitelist].coords
                probe_position_demand = (pp_dem_xy[1], pp_dem_xy[0])
                probe_position_hw = superscan._hardware_source.probe_position
                
                #todo do not use target data item
                tdi = document_controller.target_data_item
                
                # Position point region
                if probe_position_hw:
                    for point_region in tdi.graphics:
                        if ("probe" in point_region.label) or ("Probe" in point_region.label):
                            break
                else:
                    point_region = tdi.add_point_region(0, 0)
                point_region.set_property("position", probe_position_demand)
                point_region.set_property('is_position_locked', True)
                point_region.label = 'Probe position'

                # Write data_item
                try:
                    channel_name = data_item.get_metadata_value('stem.scan.channel_name')
                except KeyError:
                    channel_name = ''
                data_item.title = 'Tractor beam ({:s}) frame {:.0f}, {:s}'.format(channel_name,
                                                                                        frame_number,
                                                                            time.strftime('%H-%M-%S h'))
                metadata_dict.setdefault('Auto-Manipulator', dict())['probe_position'] = {
                                            'y': probe_position_hw.y, 'x': probe_position_hw.x }
                data_item.set_metadata(metadata_dict)
                
            frame_number += 1
            
            # HARDWARE input: set probe position
            probe_position_hw = point_region.position
                    # probe_position_hw = point_region_demand
                    #
                    #   !!! Might need this:
                    # superscan._hardware_source.probe_position = probe_position
            
            # HARDWARE action
            feedback =  keithley.waitforjump(20)
            return feedback
    
    
    current_path_idx = 0
    current_position_in_sitelist = 0
    try:
        current_path = paths[current_path_idx]
        current_sitelist = current_path.sitelist[1:len(current_path)]
        runthis = True
    except:
        runthis = False
        print("Auto-Manipulator did not start.")
  
    # Icy Manipulator
    while runthis:
        feedback = runmap(stop_event=None, frametimeout=20, jump_threshold=0.15, drift_threshold=0.1)
        if feedback == "j": # Jump detected
            current_position_in_sitelist += 1
        elif feedback == "d": # Drift detected
            #todo implement drift correction
            runthis = False            
            pass
        elif feedback == "to": # Timeout
            #todo check! retry?
            pass
        else:
            runthis = False
            pass
    
        try:
            current_sitelist[current_position_in_sitelist]
        except: # reached end of sitelist
            current_path_idx += 1
            current_position_in_sitelist = 0
            try:
                current_path = paths[current_path_idx]
                current_sitelist = current_path.sitelist[1:len(current_path)]
            except: # reached end of last path
                runthis = False
                print("FINISHED!")
