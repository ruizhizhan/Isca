import os

import numpy as np

from isca import SocratesCodeBase, DiagTable, Experiment, Namelist, GFDL_BASE
from isca.util import exp_progress

NCORES = 16
base_dir = os.path.dirname(os.path.realpath(__file__))
# a CodeBase can be a directory on the computer,
# useful for iterative development
cb = SocratesCodeBase.from_directory(GFDL_BASE)

# or it can point to a specific git repo and commit id.
# This method should ensure future, independent, reproducibility of results.
# cb = DryCodeBase.from_repo(repo='https://github.com/isca/isca', commit='isca1.1')

# compilation depends on computer specific settings.  The $GFDL_ENV
# environment variable is used to determine which `$GFDL_BASE/src/extra/env` file
# is used to load the correct compilers.  The env file is always loaded from
# $GFDL_BASE and not the checked out git repo.

# create an Experiment object to handle the configuration of model parameters
# and output diagnostics

exp = Experiment('soc_test_2', codebase=cb)
exp.clear_rundir()


#Tell model how to write diagnostics
diag = DiagTable()
#diag.add_file('atmos_daily', 1, 'days', time_units='days')
diag.add_file('atmos_step', 30, 'seconds', time_units='seconds')
#Write out diagnostics need for vertical interpolation post-processing
diag.add_field('dynamics', 'ps', time_avg=False)
diag.add_field('dynamics', 'bk')
diag.add_field('dynamics', 'pk')
diag.add_field('dynamics', 'zsurf')

diag.add_field('mixed_layer', 't_surf', time_avg=False)
diag.add_field('dynamics', 'ucomp', time_avg=False)
diag.add_field('dynamics', 'vcomp', time_avg=False)
diag.add_field('dynamics', 'omega', time_avg=False)
diag.add_field('dynamics', 'temp', time_avg=False)

#temperature tendency - units are K/s
diag.add_field('socrates', 'soc_tdt_lw', time_avg=False) # net flux lw 3d (up - down)
diag.add_field('socrates', 'soc_temp_lw', time_avg=False) # instaneous temp field
diag.add_field('socrates', 'soc_tdt_sw', time_avg=False)
diag.add_field('socrates', 'soc_tdt_rad', time_avg=False) #sum of the sw and lw heating rates
diag.add_field('socrates', 'soc_t_half', time_avg=False)
diag.add_field('socrates', 'soc_p_half', time_avg=False)
diag.add_field('socrates', 'soc_p_full', time_avg=False)
diag.add_field('socrates', 't_surf_for_soc', time_avg=False)

#net (up) and down surface fluxes
diag.add_field('socrates', 'soc_surf_flux_lw', time_avg=False)
diag.add_field('socrates', 'soc_surf_flux_sw', time_avg=False)
diag.add_field('socrates', 'soc_surf_flux_lw_down', time_avg=False)
diag.add_field('socrates', 'soc_surf_flux_sw_down', time_avg=False)
diag.add_field('socrates', 'soc_spectral_olr', time_avg=False)
#net (up) TOA and downard fluxes
diag.add_field('socrates', 'soc_olr', time_avg=False)
diag.add_field('socrates', 'soc_toa_sw', time_avg=False) 
diag.add_field('socrates', 'soc_toa_sw_down', time_avg=False)
diag.add_field('socrates', 'soc_flux_lw', time_avg=False)
diag.add_field('socrates', 'soc_flux_sw', time_avg=False)
diag.add_field('socrates', 'soc_flux_lw_up', time_avg=False)
diag.add_field('socrates', 'soc_flux_sw_up', time_avg=False)
diag.add_field('socrates', 'soc_coszen', time_avg=False)
exp.diag_table = diag

#Define values for the 'core' namelist
"""sp_test_root = 'src/atmos_param/socrates/src/trunk/data/spectra/sp_test/'
star_gas = '55CancriA'"""
exp.namelist = namelist = Namelist({
    'main_nml':{
     'days'   : 0,
     'hours'  : 0,
     'minutes': 0,
     'seconds': 30,
     'dt_atmos':30,
     'current_date' : [1,1,1,0,0,0],
     'calendar' : 'thirty_day'
    },
    'socrates_rad_nml': {
        'stellar_constant':50*1370.,
        'lw_spectral_filename':os.path.join(GFDL_BASE,'src/atmos_param/socrates/src/trunk/data/spectra/ga7/sp_lw_ga7'),
        'sw_spectral_filename':os.path.join(GFDL_BASE,'src/atmos_param/socrates/src/trunk/data/spectra/ga7/sp_sw_ga7'),
        'do_read_ozone': False,
        'dt_rad':30, # 600
        'store_intermediate_rad':True,
        'chunk_size': 16,
        'use_pressure_interp_for_half_levels':False,
        'tidally_locked':False,
        'solday':90,
        'inc_o3': False, 
        'inc_h2o': False,
        'inc_co2': True,
        'inc_co': True,
        'account_for_effect_of_water': False, # still water in the atm, not just disable the radiation; ask stephen: h2o; check the rain-> small value; email metoffice again
        'account_for_effect_of_ozone': False,
        'co_mix_ratio': 0.0,  #  mixed gas concentrations (kg / kg)
        'co2_ppmv': 1e6,
        
        'n2o_mix_ratio':0.0,'ch4_mix_ratio':0.0,'o2_mix_ratio':0.0, 
        'so2_mix_ratio':0.0,'cfc11_mix_ratio':0.0, 'cfc12_mix_ratio':0.0, 
        'cfc113_mix_ratio':0.0,'hcfc22_mix_ratio':0.0, 
    }, 
    'spectral_init_cond_nml': {
        'initial_temperature': 200
    },
    
    'astronomy_nml': {
        'ecc': 0.0,
        'obliq': 0.0
    },
    'constants_nml': {
        'radius': 1*6371.e3, # form?
        'grav': 1*9.81,
        'omega': 2.*np.pi/(1*24.*3600.), # [s^-1]
        'orbital_period': 1*24.*3600., # [s]
        'solar_const': 0.5*1370., # [W/m^2]
        'rdgas': 8.314/44e-3, # gas constant for CO2 [J/kg/K]
        'kappa': 2./9. # R/c_p depends on the molecule
    },
    'idealized_moist_phys_nml': {
        'do_damping': True,
        'turb':True,
        'mixed_layer_bc':True,
        'do_virtual' :False,
        'do_simple': True,
        'roughness_mom':3.21e-05,
        'roughness_heat':3.21e-05,
        'roughness_moist':3.21e-05,            
        'two_stream_gray': False,     #Use the grey radiation scheme
        'do_socrates_radiation': True,
        'convection_scheme': 'DRY', #Use dry convection               
    },

    'vert_turb_driver_nml': {
        'do_mellor_yamada': False,     # default: True
        'do_diffusivity': True,        # default: False
        'do_simple': True,             # default: False
        'constant_gust': 0.0,          # default: 1.0
        'use_tau': False
    },

    'diffusivity_nml': {
        'do_entrain':False,
        'do_simple': True,
    },

    'surface_flux_nml': {
        'use_virtual_temp': False,
        'do_simple': True,
        'old_dtaudv': True,
        'use_actual_surface_temperatures': False, 
    },

    'atmosphere_nml': {
        'idealized_moist_model': True
    },

    #Use a large mixed-layer depth, and the Albedo of the CTRL case in Jucker & Gerber, 2017
    'mixed_layer_nml': {
        'tconst' : 285.,
        'prescribe_initial_dist':True,
        'evaporation':False,  
        'depth': 0.5,                          #Depth of mixed layer used
        'albedo_value': 0.0,                  #Albedo value used      
    },

    'qe_moist_convection_nml': {
        'rhbm':0.7,
        'Tmin':160.,
        'Tmax':350.   
    },
    
    'lscale_cond_nml': {
        'do_simple':True,
        'do_evap':False,
    },
    
    'sat_vapor_pres_nml': {
        'do_simple':True,
        'do_not_calculate':True, #turn of esat calc altogether (for exoplanets where temperatures will be outside valid range)
    },
    
    'damping_driver_nml': {
        'do_rayleigh': True,
        'trayfric': -0.5,              # neg. value: time in *days*
        'sponge_pbottom':  150., #Setting the lower pressure boundary for the model sponge layer in Pa.
        'do_conserve_energy': True,      
    },

    # FMS Framework configuration
    'diag_manager_nml': {
        'mix_snapshot_average_fields': False  # time avg fields are labelled with time in middle of window
    },

    'fms_nml': {
        'domains_stack_size': 600000                        # default: 0
    },

    'fms_io_nml': {
        'threading_write': 'single',                         # default: multi
        'fileset_write': 'single',                           # default: multi
    },

    'spectral_dynamics_nml': {
        'damping_order': 4,
        'damping_coeff': 2.3148148e-04,      
        'water_correction_limit': 200.e2,
        'reference_sea_level_press':1e5,
        'num_levels':40,      #How many model pressure levels to use
        'valid_range_t':[0.,1000.],
        'initial_sphum':[0.], # set to zero
        'vert_coord_option':'uneven_sigma',
        'surf_res':0.2, # Parameter that sets the vertical distribution of sigma levels
        'scale_heights' : 4.0, # test scale height
        'exponent':2.0,
        'robert_coeff':0.03,
        'do_water_correction': False # disable water correction
    },

})

#Lets do a run!
if __name__=="__main__":

        cb.compile(debug=False)
        #Set up the experiment object, with the first argument being the experiment name.
        #This will be the name of the folder that the data will appear in.

        exp.run(71, num_cores=NCORES, overwrite_data=False)
        
        for i in range(72,81):
            exp.run(i, num_cores=NCORES, overwrite_data=False)