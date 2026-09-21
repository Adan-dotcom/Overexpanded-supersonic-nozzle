print('Products/air compressible mixing benchmark: configure transient solve.')

config.dimensions = 2
config.axisymmetric = false
config.solver_mode = 'transient'

local nsp, nmodes, gmodel = setGasModel('gas-model.lua')
print('Gas model species=', nsp, ' energy modes=', nmodes)

-- Exhaust composition is the normalized retained-species composition at the
-- CEA exit of hot_methalox_nominal_022.  The omitted trace fraction is
-- 7.391e-7.  See README.md for the selection rule and evidence paths.
local products_massf = {
   H2O=0.439433324785,
   CO2=0.367490271612,
   CO=0.182304134741,
   H2=0.0107250079269,
   OH=3.93300290688e-5,
   O2=1.49400110422e-7,
   O=3.65000269772e-8,
   H=7.74500572433e-6,
   N2=0.0
}
local air_massf = {N2=0.767, O2=0.233}

-- Equal static pressure isolates a canonical mixing layer from nozzle pressure
-- mismatch.  Mach 2 on both sides makes both west-face conditions supersonic;
-- differing temperatures and molecular weights create the velocity shear.
local p_common = 100836.186539 -- Pa, DOE ambient pressure for nominal_022
local products_T = 1738.69    -- K, CEA exit temperature for nominal_022
local air_T = 300.0           -- K, documented benchmark reference state
local inflow_mach = 2.0

local products_gas = GasState:new{gmodel}
products_gas.p = p_common
products_gas.T = products_T
products_gas.massf = products_massf
gmodel:updateThermoFromPT(products_gas)
gmodel:updateSoundSpeed(products_gas)

local air_gas = GasState:new{gmodel}
air_gas.p = p_common
air_gas.T = air_T
air_gas.massf = air_massf
gmodel:updateThermoFromPT(air_gas)
gmodel:updateSoundSpeed(air_gas)

local products = FlowState:new{
   p=p_common, T=products_T, velx=inflow_mach*products_gas.a,
   massf=products_massf
}
local air = FlowState:new{
   p=p_common, T=air_T, velx=inflow_mach*air_gas.a,
   massf=air_massf
}

print(string.format('Products inflow: a=%.6g m/s, u=%.6g m/s',
                    products_gas.a, inflow_mach*products_gas.a))
print(string.format('Air inflow: a=%.6g m/s, u=%.6g m/s',
                    air_gas.a, inflow_mach*air_gas.a))

local flowDict = {products=products, air=air}
local bcDict = {
   products_inflow=InFlowBC_Supersonic:new{flowState=products},
   air_inflow=InFlowBC_Supersonic:new{flowState=air},
   outflow=OutFlowBC_Simple:new{},
   slip_wall=WallBC_WithSlip:new{}
}
makeFluidBlocks(bcDict, flowDict)
mpiDistributeBlocks{ntasks=6}

config.flux_calculator = 'adaptive_hanel_ausmdv'
config.interpolation_order = 2
config.thermo_interpolator = 'rhop'
config.viscous = true
config.spatial_deriv_locn = 'cells'
config.spatial_deriv_calc = 'least_squares'

-- Laminar multicomponent diffusion uses the binary coefficients supplied by
-- the same explicit thermally-perfect gas model used by the flow solver.
config.mass_diffusion_model = 'ficks_first_law'
config.diffusion_coefficient_type = 'binary_diffusion'

config.gasdynamic_update_scheme = 'classic_rk3'
config.cfl_value = 0.5
config.dt_init = 1.0e-10
config.max_step = 200000

-- The initial field already contains the two correct streams throughout the
-- domain. One complete air-stream transit removes downstream dependence on
-- that initialization; another 0.5 transit provides development margin while
-- keeping the measured six-rank runtime inside the 10--30 minute screen target.
local domain_length = 0.120
local air_velocity = inflow_mach*air_gas.a
local flow_time = domain_length/air_velocity
config.max_time = 1.5*flow_time
config.dt_plot = config.max_time/8.0

print(string.format('Reference flow time: %.9g s; max_time: %.9g s',
                    flow_time, config.max_time))
