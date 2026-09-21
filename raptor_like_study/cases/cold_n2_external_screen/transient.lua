print('DLR-PAR cold-N2 external-plume transient screen')
dofile('run_parameters.lua')

config.dimensions = 2
config.axisymmetric = true
config.solver_mode = screen.solver_mode
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
if screen.initial_solution_dir then
   -- Official fine-grid continuation pattern:
   -- examples/lmr/2D/diffuser-busemann/fine-grid/job.lua
   flowDict.initial = FlowSolution:new{
      dir=screen.initial_solution_dir,
      snapshot='final',
      nBlocks=9,
      make_kdtree=true
   }
end
local bcDict = {
   inlet=InFlowBC_FromStagnation:new{stagnationState=reservoir},
   ambient=InOutFlowBC_Ambient:new{flowState=ambient_state},
   outflow=OutFlowBC_Simple:new{},
   wall=wall_bc
}
makeFluidBlocks(bcDict, flowDict)
mpiDistributeBlocks{ntasks=6}

-- Stage 1 keeps the official underexpanded-jet transient controls exactly.
-- Wall-mesh qualification uses the official Mabey k-log-omega Newton/Krylov
-- settings from examples/lmr/2D/flat-plate-turbulent-mabey/job.lua, starting
-- from an interpolated transient solution.
if screen.solver_mode == 'steady' then
   config.flux_calculator = 'ausmdv'
   config.apply_entropy_fix = false
   config.interpolation_order = 2
   config.extrema_clipping = false
elseif screen.stage == 1 then
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

if screen.solver_mode == 'steady' then
   NewtonKrylovGlobalConfig{
      number_of_phases = 3,
      max_steps_in_initial_phases = {500, 500},
      phase_changes_at_relative_residual = {1.0e-3, 1.0e-6},
      use_preconditioner = true,
      preconditioner_perturbation = 1.0e-50,
      preconditioner = 'ilu',
      ilu_fill = 0,
      max_newton_steps = 2000,
      max_consecutive_bad_steps = 10,
      stop_on_relative_residual = 1.0e-10,
      frechet_derivative_perturbation = 1.0e-50,
      use_scaling = true,
      max_linear_solver_iterations = 100,
      max_linear_solver_restarts = 0,
      inviscid_cfl_only = true,
      use_line_search = true,
      line_search_order = 3,
      use_physicality_check = true,
      allowable_relative_mass_change = 0.9,
      min_relaxation_factor_for_update = 0.1,
      min_relaxation_factor_for_cfl_growth = 0.5,
      number_of_steps_for_setting_reference_residuals = 5,
      steps_between_status = 1,
      write_loads = true,
      total_snapshots = 5,
      steps_between_snapshots = 50,
      steps_between_diagnostics = 1
   }
   NewtonKrylovPhase:new{
      frozen_preconditioner = true,
      use_adaptive_preconditioner = true,
      steps_between_preconditioner_update = 5,
      linear_solve_tolerance = 1.0e-2,
      residual_interpolation_order = 2,
      jacobian_interpolation_order = 1,
      use_residual_smoothing = true,
      use_auto_cfl = true,
      use_local_timestep = true,
      threshold_relative_residual_for_cfl_growth = 0.9,
      start_cfl = 1.0,
      max_cfl = 1.0e6,
      auto_cfl_exponent = 0.75
   }
   NewtonKrylovPhase:new{
      residual_interpolation_order = 2,
      jacobian_interpolation_order = 2,
      use_residual_smoothing = false,
      start_cfl = -1.0
   }
   NewtonKrylovPhase:new{
      frozen_shock_detector = true,
      frozen_limiter_for_residual = true,
      frozen_limiter_for_jacobian = true,
      start_cfl = -1.0
   }
end

print(string.format('stage=%d Pa=%.9g NPR=%.9g P0=%.9g T0=%.9g',
                    screen.stage, screen.pa_Pa, screen.npr,
                    screen.p0_Pa, screen.T0_K))
print(string.format('Tu=%.9g L=%.9g k=%.9g omega_linear=%.9g mu_t/mu=%.9g',
                    screen.turbulence_intensity,
                    screen.turbulence_length_scale_m,
                    tke, omega_from_length, turb_lam_viscosity_ratio))
