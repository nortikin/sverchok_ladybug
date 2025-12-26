bl_info = {
    "name": "Ladybug Tools",
    "author": "Dion Moult",
    "version": (0, 0, 240529),
    "blender": (2, 90, 0),
    "location": "Node Editor",
    "category": "Node",
    "description": "Ladybug, Honeybee, Butterfly, and Dragonfly for Blender",
    "warning": "",
    "wiki_url": "https://wiki.osarch.org/",
    "tracker_url": "https://github.com/ladybug-tools/ladybug-blender"
}

import os
import site

cwd = os.path.dirname(os.path.realpath(__file__))
site.addsitedir(os.path.join(cwd, "lib"))

import sys
import importlib
import nodeitems_utils
import sverchok
from ladybug_tools import icons, sockets
from sverchok.ui.nodeview_space_menu import add_node_menu
import logging
logger = logging.getLogger('sverchok')

def nodes_index():
    return [("Ladybug", [
        ("ladybug.LB_Out", "SvLBOut", "VizLB"),
        # Generated nodes
        ("ladybug.LB_Compass", "SvCompass", "ExtraLB"),
        ("ladybug.LB_Construct_Data_Type", "SvConstrType", "Analyze Data"),
        ("ladybug.LB_Deconstruct_Design_Day", "SvDecnstrDesignDay", "Import"),
        ("ladybug.LB_Legacy_Updater", "SvLegacy", "Version"),
        ("ladybug.LB_Screen_Oriented_Text", "SvText2D", "ExtraLB"),
        ("ladybug.LB_Data_DateTimes", "SvDataDT", "Analyze Data"),
        ("ladybug.LB_Wind_Speed", "SvWindSpeed", "Analyze Data"),
        ("ladybug.LB_Cumulative_Sky_Matrix", "SvSkyMatrix", "Visualize Data"),
        ("ladybug.LB_Open_Directory", "SvOpenDir", "ExtraLB"),
        ("ladybug.LB_PMV_Comfort", "SvPMV", "Analyze Data"),
        ("ladybug.LB_HOY_to_DateTime", "SvDateTime", "Analyze Data"),
        ("ladybug.LB_Magnetic_to_True_North", "SvTrueNorth", "ExtraLB"),
        ("ladybug.LB_View_From_Sun", "SvViewFromSun", "Analyze Geometry"),
        ("ladybug.LB_Color_Range", "SvColRange", "ExtraLB"),
        ("ladybug.LB_Thermal_Shade_Benefit", "SvThermalShadeBenefit", "Analyze Geometry"),
        ("ladybug.LB_View_Factors", "SvViewFactors", "Analyze Geometry"),
        ("ladybug.LB_Dump_VisualizationSet", "SvDumpVisSet", "ExtraLB"),
        ("ladybug.LB_Preview_VisualizationSet", "SvVisSet", "ExtraLB"),
        ("ladybug.LB_Open_File", "SvOpenFile", "ExtraLB"),
        ("ladybug.LB_Day_Solar_Information", "SvDayInfo", "Analyze Data"),
        ("ladybug.LB_Adaptive_Comfort", "SvAdaptive", "Analyze Data"),
        ("ladybug.LB_Apply_Conditional_Statement", "SvStatement", "Analyze Data"),
        ("ladybug.LB_Analysis_Period", "SvAnalysisPeriod", "Analyze Data"),
        ("ladybug.LB_Orient_to_Camera", "SvOrientCam", "ExtraLB"),
        ("ladybug.LB_Load_Data", "SvLoadData", "ExtraLB"),
        ("ladybug.LB_Solar_MRT_from_Solar_Components", "SvComponentSolarMRT", "Analyze Data"),
        ("ladybug.LB_Legend_Parameters_Categorized", "SvLegendParCategorized", "ExtraLB"),
        ("ladybug.LB_Clothing_by_Temperature", "SvCloByTemp", "Analyze Data"),
        ("ladybug.LB_Wind_Profile", "SvWindProfile", "Visualize Data"),
        ("ladybug.LB_Import_Location", "SvImportLoc", "Import"),
        ("ladybug.LB_Dump_Data", "SvDumpData", "ExtraLB"),
        ("ladybug.LB_Spatial_Heatmap", "SvHeatmap", "ExtraLB"),
        ("ladybug.LB_View_Rose", "SvViewRose", "Analyze Geometry"),
        ("ladybug.LB_PET_Body_Parameters", "SvPETPar", "ExtraLB"),
        ("ladybug.LB_Radiation_Rose", "SvRadRose", "Visualize Data"),
        ("ladybug.LB_Hourly_Plot", "SvHourlyPlot", "Visualize Data"),
        ("ladybug.LB_Wind_Rose", "SvWindRose", "Visualize Data"),
        ("ladybug.LB_Area_Aggregate", "SvAreaAgg", "ExtraLB"),
        ("ladybug.LB_Create_Legend", "SvCreateLegend", "ExtraLB"),
        ("ladybug.LB_UTCI_Comfort", "SvUTCI", "Analyze Data"),
        ("ladybug.LB_Relative_Humidity_from_Dew_Point", "SvRelHumid", "Analyze Data"),
        ("ladybug.LB_Direct_Sun_Hours", "SvDirectSunHours", "Analyze Geometry"),
        ("ladybug.LB_Sky_Dome", "SvSkyDome", "Visualize Data"),
        ("ladybug.LB_Adaptive_Chart", "SvAdaptiveChart", "Visualize Data"),
        ("ladybug.LB_PMV_Comfort_Parameters", "SvPMVPar", "ExtraLB"),
        ("ladybug.LB_PET_Comfort", "SvPET", "Analyze Data"),
        ("ladybug.LB_Directional_Solar_Irradiance", "SvDirSolar", "Analyze Data"),
        ("ladybug.LB_Filter_by_Normal", "SvFilterNormal", "ExtraLB"),
        ("ladybug.LB_Real_Time_Incident_Radiation", "SvRTrad", "Analyze Geometry"),
        ("ladybug.LB_Outdoor_Solar_MRT", "SvOutdoorSolarMRT", "Analyze Data"),
        ("ladybug.LB_Deconstruct_VisualizationSet", "SvDeconstructVisSet", "ExtraLB"),
        ("ladybug.LB_Generate_Point_Grid", "SvGenPts", "ExtraLB"),
        ("ladybug.LB_Import_Design_Day", "SvImportDesignDay", "Import"),
        ("ladybug.LB_Deconstruct_Location", "SvDecnstrLoc", "Import"),
        ("ladybug.LB_Degree_Days", "SvHDD_CDD", "Analyze Data"),
        ("ladybug.LB_Unit_Converter", "SvUnits", "ExtraLB"),
        ("ladybug.LB_To_Unit", "SvToUnit", "ExtraLB"),
        ("ladybug.LB_Time_Aggregate", "SvAggr", "ExtraLB"),
        ("ladybug.LB_Capture_View", "SvCaptureView", "ExtraLB"),
        ("ladybug.LB_Construct_Location", "SvConstrLoc", "Import"),
        ("ladybug.LB_Convert_to_Timestep", "SvToStep", "Analyze Data"),
        ("ladybug.LB_UTCI_Comfort_Parameters", "SvUTCIPar", "ExtraLB"),
        ("ladybug.LB_Set_View", "SvSetView", "ExtraLB"),
        ("ladybug.LB_Visibility_Percent", "SvVisibilityPercent", "Analyze Geometry"),
        ("ladybug.LB_Shade_Benefit", "SvShadeBenefit", "Analyze Geometry"),
        ("ladybug.LB_Apply_Analysis_Period", "SvApplyPer", "Analyze Data"),
        ("ladybug.LB_Thermal_Indices", "SvThermalIndices", "Analyze Data"),
        ("ladybug.LB_Radiant_Asymmetry", "SvRadAsymm", "Analyze Data"),
        ("ladybug.LB_Import_STAT", "SvImportSTAT", "Import"),
        ("ladybug.LB_Benefit_Sky_Matrix", "SvBenefitMatrix", "Visualize Data"),
        ("ladybug.LB_Mesh_Threshold_Selector", "SvMeshSelector", "ExtraLB"),
        ("ladybug.LB_Deconstruct_Data", "SvXData", "Analyze Data"),
        ("ladybug.LB_Legend_Parameters", "SvLegendPar", "ExtraLB"),
        ("ladybug.LB_Construct_Header", "SvConstrHeader", "Analyze Data"),
        ("ladybug.LB_Passive_Strategy_Parameters", "SvStrategyPar", "ExtraLB"),
        ("ladybug.LB_Monthly_Chart", "SvMonthlyChart", "Visualize Data"),
        ("ladybug.LB_Comfort_Statistics", "SvComfStat", "Analyze Data"),
        ("ladybug.LB_Area_Normalize", "SvNormalize", "ExtraLB"),
        ("ladybug.LB_Solar_Body_Parameters", "SvSolarBodyPar", "ExtraLB"),
        ("ladybug.LB_PMV_Polygon", "SvPMV Polygon", "Visualize Data"),
        ("ladybug.LB_EPWmap", "SvEPWMap", "Import"),
        ("ladybug.LB_Indoor_Solar_MRT", "SvIndoorSolarMRT", "Analyze Data"),
        ("ladybug.LB_Mass_Arithmetic_Operation", "SvMassArithOp", "Analyze Data"),
        ("ladybug.LB_Set_Rhino_Sun", "SvRhinoSun", "Analyze Geometry"),
        ("ladybug.LB_Radiation_Dome", "SvRadiationDome", "Visualize Data"),
        ("ladybug.LB_Psychrometric_Chart", "SvPsychrometricChart", "Visualize Data"),
        ("ladybug.LB_Deconstruct_Matrix", "SvXMatrix", "ExtraLB"),
        ("ladybug.LB_EPW_to_DDY", "SvEPWtoDDY", "Import"),
        ("ladybug.LB_SunPath", "SvSunpath", "Visualize Data"),
        ("ladybug.LB_To_IP", "SvToIP", "ExtraLB"),
        ("ladybug.LB_To_SI", "SvToSI", "ExtraLB"),
        ("ladybug.LB_Adaptive_Comfort_Parameters", "SvAdaptPar", "ExtraLB"),
        ("ladybug.LB_UTCI_Polygon", "SvUTCI Polygon", "Visualize Data"),
        ("ladybug.LB_Mesh_to_Hatch", "SvHatch", "ExtraLB"),
        ("ladybug.LB_Construct_Matrix", "SvPlusMatrix", "ExtraLB"),
        ("ladybug.LB_Human_to_Sky_Relation", "SvHumanToSky", "Analyze Geometry"),
        ("ladybug.LB_Time_Interval_Operation", "SvTimeOp", "Analyze Data"),
        ("ladybug.LB_Arithmetic_Operation", "SvArithOp", "Analyze Data"),
        ("ladybug.LB_Incident_Radiation", "SvIncidentRadiation", "Analyze Geometry"),
        ("ladybug.LB_Sky_Mask", "SvSyMask", "Analyze Geometry"),
        ("ladybug.LB_Solar_Envelope", "SvSolarEnvelope", "Analyze Geometry"),
        ("ladybug.LB_Ankle_Draft", "SvAnkleDraft", "Analyze Data"),
        ("ladybug.LB_Legend_2D_Parameters", "SvLegend2D", "ExtraLB"),
        ("ladybug.LB_Import_EPW", "SvImportEPW", "Import"),
        ("ladybug.LB_Construct_Data", "SvPlusData", "Analyze Data"),
        ("ladybug.LB_Humidity_Metrics", "SvHumidityR", "Analyze Data"),
        ("ladybug.LB_Surface_Ray_Tracing", "SvSrfRayTrace", "Analyze Geometry"),
        ("ladybug.LB_Import_DDY", "SvImportDDY", "Import"),
        ("ladybug.LB_Calculate_HOY", "SvHOY", "Analyze Data"),
        ("ladybug.LB_Download_Weather", "SvDownloadEPW", "Import"),
        ("ladybug.LB_Deconstruct_Header", "SvXHeader", "Analyze Data"),
        ("ladybug.LB_Time_Rate_of_Change", "SvRate", "ExtraLB"),
        ("ladybug.LB_View_Percent", "SvViewPercent", "Analyze Geometry"),
    ])]


def make_node_categories() -> list[dict[str, list[str]]]:
    node_categories = [{}]
    for category, nodes in nodes_index():
        subcategories = {}
        for module_name, node_name, subcategory in nodes:
            subcategories.setdefault(subcategory, []).append(node_name)
        subcategories = [{subcategory: items} for subcategory, items in subcategories.items()]
        node_categories[0][category] = subcategories

    return node_categories


node_categories = make_node_categories()


def make_node_list():
    modules = []
    base_name = "ladybug_tools.nodes"
    index = nodes_index()
    for category, items in index:
        for module_name, node_name, subcategory in items:
            module = importlib.import_module(f".{module_name}", base_name)
            modules.append(module)
    return modules

imported_modules = make_node_list()

reload_event = False

import bpy

def register_nodes():
    node_modules = make_node_list()
    for module in node_modules:
        module.register()
    logger.info("Registered %s nodes", len(node_modules))

def unregister_nodes():
    global imported_modules
    for module in reversed(imported_modules):
        module.unregister()


add_node_menu.append_from_config(node_categories)


def register():
    logger.debug("Registering ladybug_tools")

    icons.register()
    sockets.register()
    register_nodes()
    add_node_menu.register()

def unregister():
    unregister_nodes()
    sockets.unregister()
    icons.unregister()
