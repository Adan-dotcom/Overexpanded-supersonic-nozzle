print('DLR-PAR cold-N2 external-plume transient screen')
dofile('run_parameters.lua')

config.dimensions = 2
config.axisymmetric = true
config.solver_mode = 'transient'
if screen.stage == 3 then
   config.turbulence_model = 'k_log_omega'
end

local nsp, nmodes, gmodel = setGasModel('ideal-n2.gas')
local gas = GasState:new{gmodel}
gas.p = screen.p0_Pa
gas.T = screen.T0_K
gmodel:updateThermoFromPT(gas)
gmodel:updateSoundSpeed(gas)
gmodel:updateTransCoeffs(gas)

-- Mabey's official example defines k from turbulence intensity and omega via
-- rho*k/mu_t, storing log(omega) for k_log_omega.  The provisional length
-- scale fixes mu_t through the standard beta-star=0.09 k-omega scale relation;
-- the final omega assignment below remains exactly Mabey's formulation.
local gamma = gmodel:gamma(gas)
local throat_T = 2.0*screen.T0_K/(gamma + 1.0)
local velocity_scale = math.sqrt(gamma*gmodel:R(gas)*throat_T)
local tke = 1.5*(screen.turbulence_intensity*velocity_scale)^2
local beta_star = 0.09
local omega_from_length = math.sqrt(tke)/(beta_star^0.25*screen.turbulence_length_scale_m)
local mu_t = gas.rho*tke/omega_from_length
local turb_lam_viscosity_ratio = mu_t/gas.mu
local omega = gas.rho*tke/(turb_lam_viscosity_ratio*gas.mu)
if screen.stage == 3 then omega = math.log(omega) end

local reservoir, ambient_state
if screen.stage == 3 then
   reservoir = FlowState:new{p=screen.p0_Pa, T=screen.T0_K, tke=tke, omega=omega}
   ambient_state = FlowState:new{p=screen.pa_Pa, T=screen.T0_K, tke=tke, omega=omega}
else
   reservoir = FlowState:new{p=screen.p0_Pa, T=screen.T0_K}
   ambient_state = FlowState:new{p=screen.pa_Pa, T=screen.T0_K}
end
local wall_bc
if screen.stage == 1 then
   wall_bc = WallBC_WithSlip:new{group='wall'}
elseif screen.stage == 2 then
   -- Hakkinen's first viscous transient uses an adiabatic no-slip wall.
   wall_bc = WallBC_NoSlip_Adiabatic:new{group='wall'}
else
   wall_bc = WallBC_NoSlip_FixedT0:new{
      Twall=screen.wall_temperature_K, wall_function=false, group='wall'
   }
end

local flowDict = {reservoir=reservoir, ambient=ambient_state}
local bcDict = {
   inlet=InFlowBC_FromStagnation:new{stagnationState=reservoir},
   ambient=InOutFlowBC_Ambient:new{flowState=ambient_state},
   outflow=OutFlowBC_Simple:new{},
   wall=wall_bc
}
makeFluidBlocks(bcDict, flowDict)
mpiDistributeBlocks{ntasks=6}

-- Stage 1 keeps the official underexpanded-jet transient controls exactly:
-- no explicit flux/time-step knobs.  Viscous stages use the official
-- Hakkinen transient settings for the additional viscous terms.
if screen.stage == 1 then
   config.max_time = screen.max_time_s
   config.max_step = 100000
   config.dt_plot = config.max_time/10.0
else
   config.gasdynamic_update_scheme = 'classic-rk3'
   config.flux_calculator = 'adaptive'
   config.cfl_value = 1.0
   config.dt_init = 1.0e-8
   config.max_time = screen.max_time_s
   config.max_step = 200000
   config.dt_plot = config.max_time/10.0
end
config.viscous = screen.stage >= 2
if config.viscous then
   config.spatial_deriv_locn = 'vertices'
   config.spatial_deriv_calc = 'divergence'
end

-- Load output follows the official Mabey example.
config.write_loads = true
config.boundary_groups_for_loads = 'wall'

print(string.format('stage=%d Pa=%.9g NPR=%.9g P0=%.9g T0=%.9g',
                    screen.stage, screen.pa_Pa, screen.npr,
                    screen.p0_Pa, screen.T0_K))
print(string.format('Tu=%.9g L=%.9g k=%.9g omega_linear=%.9g mu_t/mu=%.9g',
                    screen.turbulence_intensity,
                    screen.turbulence_length_scale_m,
                    tke, omega_from_length, turb_lam_viscosity_ratio))
