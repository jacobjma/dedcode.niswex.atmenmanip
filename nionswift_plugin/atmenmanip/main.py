# -*- coding: utf-8 -*-
# Special thanks for coding support go to A. Mittelberger (Brow71189@github)

# standard libraries
import gettext
import logging
import threading
import time
import numpy as np
import copy
from matplotlib import pyplot as plt
#from scipy import ndimage
#import cv2 # for noise filters
#import imp

# specific application classes
from pathfindlib import pfl_interface as pf
from pathfindlib import pfl_plot as pfplt
from imgrecoglib import irl_interface as ir
from . import auto_manipulator as am

# third party libraries
# None

# local libraries
# None

_ = gettext.gettext

class AtomManipDelegate:
     
    def __init__(self, api):
        self.__api = api
        self.panel_id = "atmen-manipulation-panel"
        self.panel_name = _("ATMEN Manipulation")
        self.panel_positions = ["left", "right"]
        self.panel_position = "right"
        
        # Default values
        self.sigma = 9 # Kernel of the Gaussian blut in pixels
        self.noise_tolerance = 1e-5
        self.maxlength = 50 # Bond max length in pixels
        self.drawn_fraction = 1/3
        
        # GUI elements
        self.sigma_field = None
        self.noise_tolerance_field = None    
        self.maxlength_field = None
        self.drawn_fraction_field = None
        self.find_maxima_button = None
        self.set_sites_and_bonds_button = None
        self.auto_detect_sources_button = None
        self.add_sources_button = None
        self.add_targets_button = None
        self.find_paths_button = None
        self.open_conceptional_plot_button = None
        self.call_auto_manipulator_button = None
        self.stop_auto_manipulator_button = None
        
        # Objects that are needed to be saved
        self.source_data_item = None
        self.processed_data_item = None
        self.picobj = None
        self.sites = None
        self.bonds = None
        self.sources = None
        self.targets = None
        self.paths = None
        
        # Threads
        self.t1 = None
        self.t2 = None
        self.t3 = None
        self.t4 = None
        self.t5 = None
        
        self.t6 = None

    def create_panel_widget(self, ui, document_controller):
        self.dc = document_controller
        
        # Callback functions
        def sigma_finished(text):
            if len(text) > 0:
                try:
                    self.sigma = float(text)
                except ValueError:
                    pass
                finally:
                    self.sigma_field.text = "{:.2f}".format(self.sigma)
        def noise_tolerance_finished(text):
            if len(text) > 0:
                try:
                    self.noise_tolerance = float(text)
                except ValueError:
                    pass
                finally:
                    self.noise_tolerance_field.text = str(self.noise_tolerance)
        def maxlength_finished(text):
            if len(text) > 0:
                try:
                    self.maxlength = float(text)
                except ValueError:
                    pass
                finally:
                    self.maxlength_field.text = "{:.2f}".format(self.maxlength)
        def drawn_fraction_finished(text):
            if len(text) > 0:
                try:
                    self.drawn_fraction = float(text)
                except ValueError:
                    pass
                finally:
                    self.drawn_fraction_field.text = "{:.2f}".format(self.drawn_fraction)
        def find_maxima_clicked():
            self.get_source_image()
            self.process_and_show()
        def set_sites_bonds_clicked():
            self.set_sites_and_bonds()
        def auto_detect_sources_clicked():
            self.auto_detect_sources()
        def add_sources_clicked():
            selection = self.dc.target_display.selected_graphics
            self.add_sources(selection)
        def add_targets_clicked():
            selection = self.dc.target_display.selected_graphics
            self.add_targets(selection)
        def find_paths_clicked():
            self.find_paths()
        def open_conceptional_plot_clicked():
            self.open_conceptional_plot()
        def call_auto_manipulator_clicked():
            self.call_auto_manipulator()
        def stop_auto_manipulator_clicked():
            #self.stop_auto_manipulator()
            pass
            
        # GUI buttons
        self.find_maxima_button = ui.create_push_button_widget('Determine Maxima')
        self.find_maxima_button.on_clicked = find_maxima_clicked
        
        self.set_sites_and_bonds_button = ui.create_push_button_widget('Set Sites and Bonds')
        self.set_sites_and_bonds_button.on_clicked = set_sites_bonds_clicked
         
        self.auto_detect_sources_button = ui.create_push_button_widget('Auto-detect sources')
        self.auto_detect_sources_button.on_clicked = auto_detect_sources_clicked
        
        self.add_sources_button = ui.create_push_button_widget('Add sources')
        self.add_sources_button.on_clicked = add_sources_clicked
        
        self.add_targets_button = ui.create_push_button_widget('Add targets')
        self.add_targets_button.on_clicked = add_targets_clicked
        
        self.find_paths_button = ui.create_push_button_widget(_('Find paths'))
        self.find_paths_button.on_clicked = find_paths_clicked
 
        self.open_conceptional_plot_button = ui.create_push_button_widget('Conceptional plot')
        self.open_conceptional_plot_button.on_clicked = open_conceptional_plot_clicked
       
        self.call_auto_manipulator_button = ui.create_push_button_widget(_('Start Auto-Manipulator'))
        self.call_auto_manipulator_button.on_clicked = call_auto_manipulator_clicked
        
        self.stop_auto_manipulator_button = ui.create_push_button_widget(_('Stop Auto-Manipulator'))
        self.stop_auto_manipulator_button.on_clicked = stop_auto_manipulator_clicked
        
        # GUI labels and inputs
        self.sigma_field = ui.create_line_edit_widget()
        self.sigma_field.text = "{:.2f}".format(self.sigma)
        self.sigma_field.on_editing_finished = sigma_finished
        self.noise_tolerance_field = ui.create_line_edit_widget()
        self.noise_tolerance_field.text = str(self.noise_tolerance)
        self.noise_tolerance_field.on_editing_finished = noise_tolerance_finished
        
        self.maxlength_field = ui.create_line_edit_widget()
        self.maxlength_field.text = "{:.2f}".format(self.maxlength)
        self.maxlength_field.on_editing_finished = maxlength_finished
        self.drawn_fraction_field = ui.create_line_edit_widget()
        self.drawn_fraction_field.text = "{:.2f}".format(self.drawn_fraction)
        self.drawn_fraction_field.on_editing_finished = drawn_fraction_finished
        
        # GUI init
        main_col = ui.create_column_widget()
        
        # Image recognition row
        ir_row = ui.create_row_widget()
        ir_row_input_col = ui.create_column_widget()
        ir_row_input_col_sig_row = ui.create_row_widget()
        ir_row_input_col_noisetol_row = ui.create_row_widget()
        ir_row_button_col = ui.create_column_widget()
        
        ir_row_input_col_sig_row.add(ui.create_label_widget(_('Sigma ')))
        ir_row_input_col_sig_row.add(self.sigma_field)
        
        ir_row_input_col_noisetol_row.add(ui.create_label_widget(_('Noise tolerance ')))
        ir_row_input_col_noisetol_row.add(self.noise_tolerance_field)
        
        ir_row_input_col.add(ir_row_input_col_sig_row)
        ir_row_input_col.add_spacing(2)
        ir_row_input_col.add(ir_row_input_col_noisetol_row)
        ir_row_input_col.add_stretch()
        
        ir_row_button_col.add_spacing(15)
        ir_row_button_col.add(self.find_maxima_button)
        ir_row_button_col.add_stretch()
    
        ir_row.add_spacing(5)
        ir_row.add(ir_row_input_col)
        ir_row.add_spacing(2)
        ir_row.add(ir_row_button_col)
        ir_row.add_stretch()
        
        # Sites and bonds row
        sb_row = ui.create_row_widget()
        sb_row_input_col = ui.create_column_widget()
        sb_row_input_col_maxlength_row = ui.create_row_widget()
        sb_row_input_col_drawn_fraction_row = ui.create_row_widget()
        sb_row_button_col = ui.create_column_widget()
        
        sb_row_input_col_maxlength_row.add(ui.create_label_widget(_('Max. bond length (in px) ')))
        sb_row_input_col_maxlength_row.add(self.maxlength_field)
        
        sb_row_input_col_drawn_fraction_row.add(ui.create_label_widget(_('Drawn fraction ')))
        sb_row_input_col_drawn_fraction_row.add(self.drawn_fraction_field)
        
        sb_row_input_col.add(sb_row_input_col_maxlength_row)
        sb_row_input_col.add_spacing(2)
        sb_row_input_col.add(sb_row_input_col_drawn_fraction_row)
        sb_row_input_col.add_stretch()
        
        sb_row_button_col.add_spacing(15)
        sb_row_button_col.add(self.set_sites_and_bonds_button)
        sb_row_button_col.add_stretch()
    
        sb_row.add_spacing(5)
        sb_row.add(sb_row_input_col)
        sb_row.add_spacing(2)
        sb_row.add(sb_row_button_col)
        sb_row.add_stretch()
        
        # Sources and targets row
        st_row = ui.create_row_widget()
        st_row.add_spacing(5)
        st_row.add(self.add_targets_button)
        st_row.add_spacing(2)
        st_row.add(self.add_sources_button)
        st_row.add_spacing(2)
        st_row.add(self.auto_detect_sources_button)
        st_row.add_stretch()
        
        # Path finding row
        pf_row = ui.create_row_widget()
        pf_row.add_spacing(5)
        pf_row.add(self.find_paths_button)
        pf_row.add_stretch()
        
        # Conceptional plot row
        cp_row = ui.create_row_widget()
        cp_row.add_spacing(5)
        cp_row.add(self.open_conceptional_plot_button)
        cp_row.add_stretch()
        
        # Auto-Manipulator row
        am_row = ui.create_row_widget()
        am_row.add_spacing(5)
        am_row.add(self.call_auto_manipulator_button)
        am_row.add_spacing(2)
        am_row.add(self.stop_auto_manipulator_button)
        am_row.add_stretch()
        
        # Placeholder for new rows
        pass
        
        # Building main column
        main_col.add(ir_row)
        main_col.add_spacing(2)
        main_col.add(sb_row)
        main_col.add_spacing(2)
        main_col.add(st_row)
        main_col.add_spacing(2)
        main_col.add(pf_row)
        main_col.add_spacing(2)
        main_col.add(cp_row)
        main_col.add_spacing(4)
        main_col.add(am_row)
        pass #TODO new rows come added here
        main_col.add_stretch()

        return main_col
            
    def get_source_image(self):
        try:
            self.source_data_item = self.dc.target_data_item
        except AttributeError:
            self.source_data_item = None
    
    # Determine maxima       
    def process_and_show(self):
        if self.source_data_item is None:
            print("No data item selected.")
            return
            
        if self.t1 is not None and self.t1.is_alive():
            print('Still working. Wait until finished.')
            return
            
        def do_this():
            if self.processed_data_item is None:
                xdata = copy.deepcopy(self.source_data_item.xdata)
                self.processed_data_item = self.dc.create_data_item_from_data_and_metadata(xdata,
                                                                title='Local Maxima of ' + self.source_data_item.title)
            self.processed_data_item.title = 'Local Maxima of ' + self.source_data_item.title
            
            #TOOD debug this. get calibration data from source data item
            #self.processed_data_item.set_dimensional_calibrations(
            #        self.source_data_item.dimensional_calibrations)
            
            self.picobj = ir.Picture(self.source_data_item.data, self.source_data_item.title,\
                                self.sigma, self.noise_tolerance)
            print(' Blurring and finding maxima...')
            self.picobj.blur_image()
            self.picobj.detect_maxima()
            #picobj._plot()
            
            maxima = self.picobj.maxima[-1] #TODO: change array-behavior in image_recognition
            number_maxima = len(maxima)

            self.processed_data_item.set_data(self.picobj.pic_filtered[-1])
            if number_maxima < 3000:
                #logging.info('Found {:.0f} maxima'.format(number_maxima))
                pass
            else:
                logging.info(
                        'Found {:.0f} maxima (only showing {:.0f} for performance reasons)'.format(number_maxima,
                                                                             number_maxima//((number_maxima//3000)+1)))
            
            with self.dc.library.data_ref_for_data_item(self.processed_data_item):
                shape = self.processed_data_item.xdata.data_shape
                for region in self.processed_data_item.regions:
                    if region.type in ('point-region', 'ellipse-region', 'line-region', 'rectangle-region'):
                        try:
                            self.processed_data_item.remove_region(region)
                        except:
                            pass
                for i in range(number_maxima):
                    if number_maxima < 3000 or i%((number_maxima//3000)+1) == 0:
                        loc = maxima[i]
                        self.processed_data_item.add_point_region(
                                loc[0]/shape[0], loc[1]/shape[1])
        
        self.t1 = threading.Thread(target = do_this, name = 'dothis')
        self.t1.start()
        
    # Sites and bonds
    #TODO: secure that site-graphics assignment stays consistent, look near the comment lines "# Mutual assignment"
    def set_sites_and_bonds(self):
        if self.processed_data_item is None:
            print("Aborted! Determine maxima first.")
            return
        if self.t2 is not None and self.t2.is_alive():
            print('Still working. Wait until finished.')
            return
        
        maxima = self.picobj.maxima[-1] #TODO see above
        
        def thread_this():
            #TODO
            # Probably it would be better to set the sites in a regular manner
            # in order to match the graphene structure.
            # (tddnqu: Relocate when compared to the actual maxima)

            # Create and assign sites and bonds
            self.sites = []
            
            with self.dc.library.data_ref_for_data_item(self.processed_data_item):
                shape = self.processed_data_item.xdata.data_shape
                
                # Delete old 
                for region in self.processed_data_item.regions:
                    if region.type in ('line-region', 'rectangle-region', 'ellipse-region'):
                        try:
                            self.processed_data_item.remove_region(region)
                        except:
                            pass
                self.sources = np.array([])
                self.targets = np.array([])
                
                # Set sites
                print("======= Set sites =======")
                for i in range(len(maxima)):
                    thissite = pf.Site(maxima[i][0], maxima[i][1],
                                          max_bond_radius = self.maxlength)
                    self.sites.append(thissite)
                    
                    # Mutual assignment
                    self.sites[-1].uuid_graphics = self.processed_data_item.regions[i].uuid #TODO: rework! not sure whether correct point_graphics is taken.
                    self.processed_data_item.regions[i].graphic_id = len(self.sites) #TODO: maybe change somehow. Attribute graphic_id is abused

                # Set bonds
                print("======= Set and display bonds =======")
                self.bonds = pf.Bonds(self.sites, self.maxlength)

                for b in self.bonds.members:
                    y1 = b.coords()[0][0]
                    x1 = b.coords()[0][1]
                    y2 = b.coords()[1][0]
                    x2 = b.coords()[1][1]
                    # shorten the display of the bond
                    w = (1 - self.drawn_fraction) / 2 # weight of the other position
                    #TODO: This does not work exact. Swift issue?
                    y1 = y1*(1-w) + y2*w
                    x1 = x1*(1-w) + x2*w
                    y2 = y1*w + y2*(1-w)
                    x2 = x1*w + x2*(1-w)
                    # scale
                    y1 /= shape[0]
                    y2 /= shape[0]
                    x1 /= shape[1]
                    x2 /= shape[1]
                    self.processed_data_item.add_line_region(y1, x1, y2, x2)
        self.t2 = threading.Thread(target = thread_this, name = 'dothat')
        self.t2.start()
    
    # Auto-detect and display sources
    def auto_detect_sources(self):
        maxima = self.picobj.maxima[-1] #TODO see above
        self.picobj.detect_substitutionals()
        indx_foreigns = self.picobj.indx_substitutionals[-1] #TODO change array-behavior
        print("indices foreigns  " + str(indx_foreigns))
        
        shape = self.processed_data_item.xdata.data_shape
        ellipse_relative_size = 0.05
        for i in indx_foreigns:
            loc = maxima[i] #TODO: probably change to self.sites[i].coords
            #TODO: rework!!! unsure if correct point_graphics is taken
            thisatom = pf.Atom(self.sites[i], 'dummy-element')
            self.sources = np.append(self.sources, thisatom)
            reg = self.processed_data_item.add_rectangle_region(
                            loc[0]/shape[0], loc[1]/shape[1],
                            ellipse_relative_size, ellipse_relative_size)
                    
            # Mutual assignment
            reg.graphic_id = np.size(self.sources)
            self.sources[-1].uuid_graphic = reg.uuid #TODO: see above
            
    # Add sources
    def add_sources(self, selection):
        if self.processed_data_item is None:
            print("Aborted! Determine maxima first.")
            return
        if self.t3 is not None and self.t3.is_alive():
            print('Still working. Wait until finished.')
            return
        
        def thread_this():
            if self.sources is None:
                self.sources = np.array([])
            
            ellipse_relative_size = 0.05
            for s in selection:
                loc = s.position
                thisatom = pf.Atom(self.sites[eval(s.graphic_id)], 'dummy-element')
                self.sources = np.append(self.sources, thisatom) 
                reg = self.processed_data_item.add_rectangle_region(
                        loc[0], loc[1],
                        ellipse_relative_size, ellipse_relative_size)
                
                # Mutual assignment
                reg.graphic_id = np.size(self.sources) #TODO: attribute graphic_id is abused
                self.sources[-1].uuid_graphic = reg.uuid #TODO: see above
                
        self.t3 = threading.Thread(target = thread_this)
        self.t3.start()
        
    # Add targets
    def add_targets(self, selection):
        if self.processed_data_item is None:
            print("Aborted! Determine maxima first.")
            return
        if self.t4 is not None and self.t4.is_alive():
            print('Still working. Wait until finished.')
            return
        
        def thread_this():
            if self.targets is None:
                self.targets = np.array([])
            
            ellipse_relative_size = 0.05
            for s in selection:
                loc = s.position
                idx_site = eval(s.graphic_id)
                thissite = self.sites[idx_site]
                self.targets = np.append(self.targets, thissite)
                reg = self.processed_data_item.add_ellipse_region(
                        loc[0], loc[1],
                        ellipse_relative_size, ellipse_relative_size)
                
                # Mutual assignment
                reg.graphic_id = idx_site #TODO: attribute graphic_id is abused
                #TODO: not sure whether idx of self.targets-array or self.sites-array should be taken
                self.targets[-1].uuid_graphic = reg.uuid #TODO: see above
                
        self.t4 = threading.Thread(target = thread_this)
        self.t4.start()  
    
    # Path finding
    def find_paths(self):
        if (self.sources is None) or (self.targets is None):
            print("Aborted! Set sources and targets.")
            return
        if self.t5 is not None and self.t5.is_alive():
            print('Still working. Wait until finished.')
            return
        
        def thread_this():
            try:
                print(len(self.sources))
                print(len(self.targets))
                self.paths = pf.MultiplePaths_NoOverlap(self.sources, self.targets)
            except ValueError as e:
                print(e)
                return
            else:
                self.paths.determine_paths()
        self.t5 = threading.Thread(target = thread_this)
        self.t5.start()
        
    # Auto-Manipulator
    def call_auto_manipulator(self):
        def thread_that():
            try:
                am.AM(self.paths, self.api)
                logging.info("Calling Auto-Manipulator...")
            except:
                logging.info("Error #002")
        self.t6 = threading.Thread(target = thread_that)
        self.t6.start()
        
    # Conceptional plot
    def open_conceptional_plot(self):
        def pfplt_func():
            fig = plt.figure() # 57 = pf
            ax = fig.add_subplot(1, 1, 1)
            pfplt.plt_sites(ax, self.sites)
            pfplt.plt_bonds(ax, self.bonds)
            pfplt.plt_sources(ax, self.sources)
            pfplt.plt_targets(ax, self.targets)
            plt.gca().invert_yaxis()
            try:
                plt.show()
            except:
                pass
        pfplt_func() # This does only work in the main thread !
        print("Opening conceptional plot finished.")
        

class AtomManipExtension(object):
    
    # required for Swift to recognize this as an extension class.
    extension_id = "nion.swift.extension.atom_manipulation"
    
    def __init__(self, api_broker):
        # grab the api object.
        api = api_broker.get_api(version='~1.0', ui_version='~1.0')
        # be sure to keep a reference or it will be closed immediately.
        self.__panel_ref = api.create_panel(AtomManipDelegate(api))
  
    def close(self):
        # close will be called when the extension is unloaded. in turn, close any references so they get closed. this
        # is not strictly necessary since the references will be deleted naturally when this object is deleted.
        self.__panel_ref.close()
        self.__panel_ref = None 
