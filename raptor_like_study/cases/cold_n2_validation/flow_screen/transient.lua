print('DLR-PAR provisional cold-N2 internal-domain RANS screen')

dofile('run_parameters.lua')
config.dimensions = 2
config.axisymmetric = true
config.solver_mode = 'steady'
config.turbulence_model = 'k_log_omega'

local nsp, nmodes, gmodel = setGasModel('gas-model.lua')
local gas = GasState:new{gmodel}
gas.p = screen.pa_Pa
gas.T = screen.T0_K
gmodel:updateThermoFromPT(gas)
gmodel:updateSoundSpeed(gas)
gmodel:updateTransCoeffs(gas)

-- The inlet intensity needs a velocity scale even though the boundary is
-- specified by stagnation state. Use the subsonic quasi-1D inlet velocity for
-- Ainlet/Athroat=4, derived from ideal-gas area-Mach theory.
local gamma = gmodel:gamma(gas)
local gas_R = gmodel:R(gas)
local function area_ratio(M)
   local exponent = (gamma + 1.0)/(2.0*(gamma - 1.0))
   local term = (2.0/(gamma + 1.0))*(1.0 + 0.5*(gamma - 1.0)*M*M)
   return (1.0/M)*term^exponent
end
local lo, hi = 1.0e-6, 0.999999
for iteration=1,100 do
   local mid = 0.5*(lo + hi)
   if area_ratio(mid) > 4.0 then lo = mid else hi = mid end
end
local inlet_M = 0.5*(lo + hi)
local inlet_T = screen.T0_K/(1.0 + 0.5*(gamma - 1.0)*inlet_M*inlet_M)
local inlet_velocity = inlet_M*math.sqrt(gamma*gas_R*inlet_T)
local tke = 1.5*(screen.turbulence_intensity*inlet_velocity)^2
local Cmu = 0.09
local omega = math.sqrt(tke)/(Cmu^0.25*screen.turbulence_length_scale_m)
local log_omega = math.log(omega)

local stagnation = FlowState:new{
   p=screen.p0_Pa, T=screen.T0_K, tke=tke, omega=log_omega
}
local inlet_pressure = screen.p0_Pa/
   (1.0 + 0.5*(gamma - 1.0)*inlet_M*inlet_M)^(gamma/(gamma - 1.0))
local initial = FlowState:new{
   p=inlet_pressure, T=inlet_T, velx=inlet_velocity,
   tke=tke, omega=log_omega
}
local wall_bc
if screen.wall_type == 'adiabatic' then
   wall_bc = WallBC_NoSlip_Adiabatic0:new{group='wall'}
else
   wall_bc = WallBC_NoSlip_FixedT0:new{
      Twall=screen.wall_temperature_K, wall_function=false, group='wall'
   }
end

local flowDict = {initial=initial}
local bcDict = {
   inlet=InFlowBC_FromStagnation:new{stagnationState=stagnation},
   outlet=OutFlowBC_FixedP:new{p_outside=screen.pa_Pa},
   wall=wall_bc
}
makeFluidBlocks(bcDict, flowDict)
mpiDistributeBlocks{ntasks=6}

config.flux_calculator = 'ausmdv'
config.interpolation_order = 2
config.thermo_interpolator = 'rhop'
config.extrema_clipping = false
config.viscous = true
config.spatial_deriv_locn = 'cells'
config.spatial_deriv_calc = 'least_squares'
config.include_boundary_faces_in_spatial_deriv_correction = true
config.write_loads = true
config.boundary_groups_for_loads = 'wall'

NewtonKrylovGlobalConfig{
   number_of_phases = 2,
   max_steps_in_initial_phases = {300},
   phase_changes_at_relative_residual = {1.0e-3},
   max_newton_steps = 1200,
   max_consecutive_bad_steps = 20,
   stop_on_relative_residual = 1.0e-6,
   number_of_steps_for_setting_reference_residuals = 5,
   use_preconditioner = true,
   preconditioner_perturbation = 1.0e-30,
   preconditioner = 'ilu',
   ilu_fill = 1,
   use_scaling = true,
   use_line_search = true,
   use_physicality_check = true,
   max_linear_solver_iterations = 100,
   steps_between_status = 1,
   steps_between_diagnostics = 1,
   total_snapshots = 5,
   steps_between_snapshots = 100,
   write_loads = true
}
NewtonKrylovPhase:new{
   residual_interpolation_order = 1,
   jacobian_interpolation_order = 1,
   frozen_preconditioner = true,
   use_adaptive_preconditioner = true,
   steps_between_preconditioner_update = 5,
   linear_solve_tolerance = 0.1,
   use_residual_smoothing = true,
   use_auto_cfl = true,
   use_local_timestep = true,
   threshold_relative_residual_for_cfl_growth = 0.95,
   start_cfl = 0.5,
   max_cfl = 1.0e4,
   auto_cfl_exponent = 0.75
}
NewtonKrylovPhase:new{
   residual_interpolation_order = 2,
   jacobian_interpolation_order = 2,
   frozen_preconditioner = true,
   use_adaptive_preconditioner = true,
   steps_between_preconditioner_update = 5,
   linear_solve_tolerance = 0.05,
   use_residual_smoothing = false,
   use_auto_cfl = true,
   use_local_timestep = true,
   threshold_relative_residual_for_cfl_growth = 0.95,
   start_cfl = -1.0,
   max_cfl = 1.0e5,
   auto_cfl_exponent = 0.75
}

print(string.format('Pa=%.9g Pa NPR=%.9g P0=%.9g Pa T0=%.9g K',
                    screen.pa_Pa, screen.npr, screen.p0_Pa, screen.T0_K))
print(string.format('Quasi-1D inlet M=%.9g velocity=%.9g m/s tke=%.9g omega=%.9g 1/s',
                    inlet_M, inlet_velocity, tke, omega))
