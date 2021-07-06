# -*- coding: utf-8 -*-
"""
Created on Sun Jun 29 08:35:57 2021

@author: xuezhicang@gmail.com
"""

import sys

import arcpy
import os


arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension  ("Spatial")



##################
#input paramaters are below
##################        
work_place =  "D://junction_angle_comparsion//junction_angles_under_different_projections//workplace_GDB_sinu_simply_mercator_measure.gdb//"
arcpy.env.workspace = work_place 

input_river_network_layers = "D://junction_angle_comparsion//junction_angles_under_different_projections//river_polylines.gdb//HydroRIVERS_v10_na_mercator"


threshold_douglas = 150#2000 #meters the data is projectrf VN lines data
buffer_cut_r = 10
buffer_ana_r = 1

results_feature = "junction_angle_points_under_mercator_projection"
##################
#input paramaters are above
##################  

#simplify the Vn line
vn_line_douglas = "vn_line_simp"
arcpy.cartography.SimplifyLine(input_river_network_layers,work_place+vn_line_douglas,"POINT_REMOVE",threshold_douglas,"","NO_KEEP" )



#buffer two circles 
intersec_pts = "inter_pts_ger"
arcpy.Intersect_analysis(work_place+vn_line_douglas , work_place+intersec_pts ,"ALL", "", "POINT")
arcpy.AddField_management(work_place+intersec_pts, "x_co", "TEXT")
arcpy.CalculateField_management(work_place+intersec_pts, "x_co","!SHAPE.CENTROID.X!","PYTHON3 ")
arcpy.AddField_management(work_place+intersec_pts, "y_co", "TEXT")
arcpy.CalculateField_management(work_place+intersec_pts, "y_co","!SHAPE.CENTROID.Y!","PYTHON3 ")
arcpy.AddField_management(work_place+intersec_pts, "x_y_co", "TEXT")
arcpy.CalculateField_management(work_place+intersec_pts, "x_y_co","!y_co!+!x_co!","PYTHON3")
arcpy.DeleteIdentical_management(work_place+intersec_pts, "x_y_co")



buffer_cut = "buffer_cut"
buffer_analysis = "buffer_ana"
arcpy.Buffer_analysis(work_place+intersec_pts, work_place+buffer_cut, str(buffer_cut_r)+" meter", "FULL","ROUND","NONE","","GEODESIC")
arcpy.Buffer_analysis(work_place+intersec_pts, work_place+buffer_analysis, str(buffer_ana_r)+" meter", "FULL", "ROUND","NONE","","GEODESIC")
arcpy.AddField_management(work_place+buffer_analysis, "geod_area", "FLOAT")  
arcpy.CalculateField_management(work_place+buffer_analysis,"geod_area", "!SHAPE.geodesicArea@SQUAREMETERS!", "PYTHON_3")

#cut the areas
cliped_vn_lines = "clip_vn_lines" 
arcpy.Clip_analysis(work_place+vn_line_douglas, work_place+buffer_cut, work_place+cliped_vn_lines)

#multipart to single_polygons
single_clip_cut_vnlines = "sing_cut_vn"
arcpy.MultipartToSinglepart_management(work_place+cliped_vn_lines,work_place+single_clip_cut_vnlines)



#get the start pts 
print("find starting points")
arcpy.AddField_management(work_place+buffer_analysis, "stpts", "SHORT")
single_clip_cut_vn_start_pts = "sing_cut_vn_stpts"
single_clip_cut_vn_start_pts_erased_centers = "sing_cut_vn_stpts_del_cent"
count_starting_pts = "SP_startPts"

arcpy.FeatureVerticesToPoints_management(work_place+single_clip_cut_vnlines, work_place+single_clip_cut_vn_start_pts, "START")
arcpy.analysis.Erase(work_place+single_clip_cut_vn_start_pts, work_place+intersec_pts, work_place + single_clip_cut_vn_start_pts_erased_centers)

arcpy.SpatialJoin_analysis(work_place+buffer_cut, work_place+single_clip_cut_vn_start_pts_erased_centers, work_place + count_starting_pts)


# and end pts
print("find ending points")
arcpy.AddField_management(work_place+buffer_analysis, "endpts", "SHORT")

single_clip_cut_vn_end_pts = "sing_cut_vn_endpts"
single_clip_cut_vn_end_pts_erased_centers = "sing_cut_vn_endpts_del_cent"

arcpy.FeatureVerticesToPoints_management(work_place+single_clip_cut_vnlines, work_place+single_clip_cut_vn_end_pts, "END")
arcpy.analysis.Erase(work_place+single_clip_cut_vn_end_pts, work_place+intersec_pts, work_place + single_clip_cut_vn_end_pts_erased_centers)
count_starting_pts_ending_pts = "SP_startPts_endPts"

arcpy.SpatialJoin_analysis(work_place + count_starting_pts, work_place+single_clip_cut_vn_end_pts_erased_centers, work_place + count_starting_pts_ending_pts)


# select pts which including 2 end pts and 1 start point
print("select 2st 1end")
arcpy.AddField_management(work_place+count_starting_pts_ending_pts, "BOOL_JA", "SHORT")
arcpy.MakeFeatureLayer_management(work_place+count_starting_pts_ending_pts, "ana_cir_lyr")

expression = "getClass(!Join_Count!,!Join_Count_1!)"
codeblock = """def getClass(Join_Count,Join_Count_1):
    if Join_Count == 2 and Join_Count_1 ==1:
        return 1
    else:
        return 0"""
arcpy.CalculateField_management("ana_cir_lyr", "BOOL_JA",expression, "PYTHON_3",codeblock)

#select those circles which BOOL_JA == 1
arcpy.MakeFeatureLayer_management (work_place+count_starting_pts_ending_pts, "ana_cir_lyr")
arcpy.SelectLayerByAttribute_management ( "ana_cir_lyr", "NEW_SELECTION", '"BOOL_JA" = 1')
buffer_ana_selected = "buffer_ana_sel"
arcpy.CopyFeatures_management("ana_cir_lyr", work_place+buffer_ana_selected)



#select inflows lines who can form the junction angles
JA_inflow_lines = "JA_inflow_lines"
arcpy.MakeFeatureLayer_management (work_place+single_clip_cut_vnlines, "sing_vn_lyr")
arcpy.MakeFeatureLayer_management (work_place+buffer_ana_selected, "ana_cir_sel_lyr")
arcpy.MakeFeatureLayer_management (work_place+single_clip_cut_vn_start_pts_erased_centers, "JA_start_pts_lyr")

arcpy.SelectLayerByLocation_management("JA_start_pts_lyr", 'intersect',"ana_cir_sel_lyr")
arcpy.SelectLayerByLocation_management("sing_vn_lyr", 'intersect',"JA_start_pts_lyr")

arcpy.CopyFeatures_management("sing_vn_lyr", work_place+JA_inflow_lines)



#split the ana_circles by the single_clip_cut_vnlines_selected
bi_sectors = "bi_sectors"
arcpy.FeatureToPolygon_management([work_place+buffer_analysis,work_place+JA_inflow_lines],work_place+bi_sectors)

#calculate the secter's area
arcpy.AddField_management(work_place+bi_sectors, "sec_area", "FLOAT")
#arcpy.CalculateField_management(work_place+bi_sectors ,"sec_area", "!SHAPE.AREA@SQUAREMETERS!", "PYTHON_3")
arcpy.CalculateField_management(work_place+bi_sectors ,"sec_area", "!SHAPE.geodesicArea@SQUAREMETERS!", "PYTHON_3")


#calcualte angles
bi_sectors_with_small_circle_info = "bi_sectors_w_cir"
arcpy.SpatialJoin_analysis(work_place+bi_sectors, work_place+buffer_analysis, work_place + bi_sectors_with_small_circle_info)

arcpy.AddField_management(work_place+bi_sectors_with_small_circle_info, "sec_jangle", "FLOAT")
arcpy.CalculateField_management(work_place+bi_sectors_with_small_circle_info, "sec_jangle", "!sec_area!*360/(!geod_area_1!)", "PYTHON_3")


#selectr the angles which are small than 180 degree
junction_angle_sectors = "junction_angle_sectors"
arcpy.MakeFeatureLayer_management(work_place+bi_sectors_with_small_circle_info, "sectors_lyr")
arcpy.SelectLayerByAttribute_management ("sectors_lyr", "NEW_SELECTION", '"sec_jangle"<=180')
arcpy.CopyFeatures_management("sectors_lyr", work_place+junction_angle_sectors )



#convert sector to points
arcpy.FeatureToPoint_management(work_place+junction_angle_sectors, work_place + results_feature, "INSIDE")
print("finished")














