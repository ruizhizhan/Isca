## Planet configuration, 55 cnce
# radius: 1.875 R_earth
# surface gravity: 2.273 g_earth
# orbital period: 0.73654625 days
# solar constant: 2441.3 S_earth
radius = 1.875
surface_g = 2.273
orbital_period = 0.73654625
S0 = 2441.3
eccentricity = 0.05
## surface pressure and TOA pressure
surface_pressure = 1.0e6 # [Pa] reference_sea_level_press
scale_heights = 4.0 # 4.0 -> 0.08ps; 6.0 -> 0.01 ps
# rayleigh drag; test to stablize the simulation
trayfric = -8640/86400 # neg. value: time in *days*; larger value -> weaker damping
sponge_pbottom = surface_pressure/1e3 # [Pa] Set the lower pressure boundary for the model sponge layer in Pa.
## time and space resolution (from grid/sound_speed 600s)
dt_rad = 40
dt_atmos = 10
RESOLUTION = 'T42', 40
## atmosphere settings
kappa = 0.27777777777777773
mole_mass = 29.6e-3 # kg/mol
rdgas = 8.314/mole_mass
# spectral files
spec_file = f"b85_co-co2_55CancriA" # co2-co mixed gas

import os
import numpy as np

from isca import SocratesCodeBase, DiagTable, Experiment, Namelist, GFDL_BASE
from isca.util import exp_progress

NCORES = 16
base_dir = os.path.dirname(os.path.realpath(__file__))
cb = SocratesCodeBase.from_directory(GFDL_BASE)

exp = Experiment('55cnce_1e6pa_1e-1co2_co', codebase=cb)
exp.clear_rundir()

#Tell model how to write diagnostics
diag = DiagTable()
diag.add_file('atmos_hourly', 1, 'hours', time_units='hours')
#diag.add_file('atmos_step', 10, 'seconds', time_units='seconds')

#Write out diagnostics need for vertical interpolation post-processing
diag.add_field('dynamics', 'ps', time_avg=True)
diag.add_field('dynamics', 'bk')
diag.add_field('dynamics', 'pk')

#Tell model which diagnostics to write
diag.add_field('mixed_layer', 't_surf', time_avg=True)
diag.add_field('dynamics', 'sphum', time_avg=True)
diag.add_field('dynamics', 'ucomp', time_avg=True)
diag.add_field('dynamics', 'vcomp', time_avg=True)
diag.add_field('dynamics', 'omega', time_avg=True)
diag.add_field('dynamics', 'temp', time_avg=True)

#temperature tendency - units are K/s
diag.add_field('socrates', 'soc_tdt_lw', time_avg=True) # net flux lw 3d (up - down)
diag.add_field('socrates', 'soc_temp_lw', time_avg=True) # instaneous temp field
diag.add_field('socrates', 'soc_tdt_sw', time_avg=True)
diag.add_field('socrates', 'soc_tdt_rad', time_avg=True) #sum of the sw and lw heating rates
diag.add_field('socrates', 'soc_t_half', time_avg=True)
diag.add_field('socrates', 'soc_p_half', time_avg=True)
diag.add_field('socrates', 'soc_p_full', time_avg=True)
diag.add_field('socrates', 't_surf_for_soc', time_avg=True)

#net (up) and down surface fluxes
diag.add_field('socrates', 'soc_surf_flux_lw', time_avg=True)
diag.add_field('socrates', 'soc_surf_flux_sw', time_avg=True)
diag.add_field('socrates', 'soc_surf_flux_lw_down', time_avg=True)
diag.add_field('socrates', 'soc_surf_flux_sw_down', time_avg=True)
diag.add_field('socrates', 'soc_spectral_olr', time_avg=True)
#net (up) TOA and downard fluxes
diag.add_field('socrates', 'soc_olr', time_avg=True)
diag.add_field('socrates', 'soc_toa_sw', time_avg=True) 
diag.add_field('socrates', 'soc_toa_sw_down', time_avg=True)
diag.add_field('socrates', 'soc_flux_lw', time_avg=True)
diag.add_field('socrates', 'soc_flux_sw', time_avg=True)
diag.add_field('socrates', 'soc_flux_lw_up', time_avg=True)
diag.add_field('socrates', 'soc_flux_sw_up', time_avg=True)
diag.add_field('socrates', 'soc_coszen', time_avg=True)


exp.diag_table = diag

#
sp_test_root = 'src/atmos_param/socrates/src/trunk/data/spectra/sp_test/'
star_gas = '55CancriA'
#Define values for the 'core' namelist
exp.namelist = namelist = Namelist({
    'main_nml':{
     'days'   : 0,
     'hours'  : 1,
     'minutes': 0,
     'seconds': 0,
     'dt_atmos':dt_atmos,  # default: 600
     'current_date' : [1,1,1,0,0,0],
     'calendar' : 'thirty_day'
    },
    'socrates_rad_nml': {
        'stellar_constant':S0*1370,
        'lw_spectral_filename':os.path.join(GFDL_BASE,sp_test_root,star_gas,f'sp_lw_{spec_file}'),
        'sw_spectral_filename':os.path.join(GFDL_BASE,sp_test_root,star_gas,f'sp_sw_{spec_file}'),
        'dt_rad':dt_rad,
        'store_intermediate_rad':True,
        'chunk_size': 16,
        'use_pressure_interp_for_half_levels':False,
        'tidally_locked':True,
        'solday':90,
        'inc_o3': False, 
        'inc_h2o': False,
        'inc_co2': True,
        'inc_co': True,
        'account_for_effect_of_water': False, # still water in the atm, not just disable the radiation; ask stephen: h2o; check the rain-> small value; email metoffice again
        'account_for_effect_of_ozone': False,
        'co_mix_ratio': 0.8513513513513513,  #  mixed gas concentrations (kg / kg)
        'co2_ppmv': 1e5, 
        #'input_co2_mmr': True, # mass mixing ratio but ppmm
        'n2o_mix_ratio':0.0,'ch4_mix_ratio':0.0,'o2_mix_ratio':0.0, 
        'so2_mix_ratio':0.0,'cfc11_mix_ratio':0.0, 'cfc12_mix_ratio':0.0, 
        'cfc113_mix_ratio':0.0,'hcfc22_mix_ratio':0.0,  
    },
    
    'spectral_init_cond_nml': {
        'initial_temperature': 2500
    },
    
    'astronomy_nml': {
        'ecc': eccentricity,
        'obliq': 0.0
    },
    
    'constants_nml': {
        'radius': radius*6371.e3, # form?
        'grav': surface_g*9.81,
        'omega': 2.*np.pi/(orbital_period*24.*3600.), # [s^-1]
        'orbital_period': orbital_period*24.*3600., # [s]
        'solar_const': S0*1370., # [W/m^2]
        'rdgas': rdgas, # gas constant for CO2 [J/kg/K]
        'kappa': kappa, # R/c_p depends on the molecule
        'es0': 1.0, # for saturation vapor pressure
    },
    
    'idealized_moist_phys_nml': {
        'do_damping': True,
        'turb':True,
        'mixed_layer_bc':True,
        'do_virtual' :False,
        'do_simple': True,
        'roughness_mom':1e-3, # rocky surface 1e-3 (?); open ocean 2e-4; plant 1e-2
        'roughness_heat':1e-3,
        'roughness_moist':1e-3,            
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
        'idealized_moist_model': True, 
    },

    #Use a large mixed-layer depth, and the Albedo of the CTRL case in Jucker & Gerber, 2017
    'mixed_layer_nml': {
        'tconst' : 2500.,                      
        'prescribe_initial_dist':True,
        'evaporation': False,                  # Disable surface evaporation
        'depth': 0.5,                          # Depth of mixed layer used
        'albedo_value': 0.0,                   # set to zero for future tests
    },

    'qe_moist_convection_nml': {
        'rhbm':0.7,
        'Tmin':160.,
        'Tmax':350.   # can't be more than 373K ?
    },
    
    'lscale_cond_nml': {
        'do_simple':True,
        'do_evap':False,
    },
    
    'sat_vapor_pres_nml': {
        'do_simple':True, # disable the calculation in the kernal code
        'do_not_calculate':True, #turn of esat calc altogether (for exoplanets where temperatures will be outside valid range)
    },
    
    'damping_driver_nml': {
        'do_rayleigh': True,
        'trayfric': trayfric,
        'sponge_pbottom':  sponge_pbottom,
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
        'damping_coeff': 2.3148148e-02,      
        'water_correction_limit': 200.e2,
        'reference_sea_level_press':surface_pressure,
        'num_levels':40,      #How many model pressure levels to use
        'valid_range_t':[1.,4500.],
        'initial_sphum':[0.], # set to zero
        'vert_coord_option':'uneven_sigma',
        'surf_res':0.2, # Parameter that sets the vertical distribution of sigma levels
        'scale_heights' : scale_heights, 
        'exponent':2.0,
        'robert_coeff':0.03,
        'do_water_correction': False # disable water correction
    },
    
    'dry_convection_nml': {
        'tau': dt_atmos,
        'small': 0.001,
    },

})

#Lets do a run!
if __name__=="__main__":
    cb.compile()
    exp.set_resolution(*RESOLUTION)
    exp.run(1, num_cores=NCORES, overwrite_data=False)
    overwrite = False
    for i in range(2,1201):
        exp.run(i, num_cores=NCORES, overwrite_data=overwrite)
