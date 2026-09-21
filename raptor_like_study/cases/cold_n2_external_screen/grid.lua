print('DLR-PAR cold-N2 external-plume screening grid')
dofile('run_parameters.lua')
dofile('mesh_parameters.lua')

config.dimensions = 2
config.axisymmetric = true

-- The internal wall is the audited user reconstruction.  The downstream
-- plume topology follows examples/lmr/2D/underexpanded-jet: a nozzle opening
-- connects directly to an exterior tank, with a back plate above the lip.
local x_inlet, x_throat, x_exit = -0.02268, 0.0, 0.12502
local r_inlet, r_throat, r_exit = 0.020, 0.010, 0.05477226
local x_far, r_far = 0.32502, 0.120

local wall_convergent = Spline2:new{filename='convergent.txt'}
local wall_divergent = Spline2:new{filename='divergent.txt'}
local axis_convergent = Line:new{p0={x=x_inlet, y=0.0}, p1={x=x_throat, y=0.0}}
local axis_divergent = Line:new{p0={x=x_throat, y=0.0}, p1={x=x_exit, y=0.0}}
local axis_external = Line:new{p0={x=x_exit, y=0.0}, p1={x=x_far, y=0.0}}
local inlet = Line:new{p0={x=x_inlet, y=0.0}, p1={x=x_inlet, y=r_inlet}}
local throat = Line:new{p0={x=x_throat, y=0.0}, p1={x=x_throat, y=r_throat}}
local nozzle_exit = Line:new{p0={x=x_exit, y=0.0}, p1={x=x_exit, y=r_exit}}
local near_far = Line:new{p0={x=x_far, y=0.0}, p1={x=x_far, y=r_exit}}
local plume_interface = Line:new{p0={x=x_exit, y=r_exit}, p1={x=x_far, y=r_exit}}
local back_plate = Line:new{p0={x=x_exit, y=r_exit}, p1={x=x_exit, y=r_far}}
local outer_far = Line:new{p0={x=x_far, y=r_exit}, p1={x=x_far, y=r_far}}
local ambient_top = Line:new{p0={x=x_exit, y=r_far}, p1={x=x_far, y=r_far}}

local patches = {
   CoonsPatch:new{north=wall_convergent, east=throat, south=axis_convergent, west=inlet},
   CoonsPatch:new{north=wall_divergent, east=nozzle_exit, south=axis_divergent, west=throat},
   CoonsPatch:new{north=plume_interface, east=near_far, south=axis_external, west=nozzle_exit},
   CoonsPatch:new{north=ambient_top, east=outer_far, south=plume_interface, west=back_plate}
}

local ni_convergent = mesh.ni_convergent
local ni_divergent = mesh.ni_divergent
local ni_external = mesh.ni_external
local nj_core = mesh.nj_core
local nj_outer = mesh.nj_outer

-- The wall meshes use the official GeometricFunction form documented in
-- gdtk/doc/geom/cluster_functions and used by the official turbulent flat
-- plate examples.  The nondimensional a value is set independently on each
-- radial edge so that the requested dimensional first-cell height is shared.
local cf_convergent, cf_divergent, cf_external = {}, {}, {}
if mesh.wall_first_cell_m then
   -- r=1.3 is the official laminar-flat-plate value; it also leaves enough
   -- nodes for the very small first cell before the distribution becomes
   -- uniform across the core.
   local growth = 1.3
   cf_convergent = {
      south=RobertsFunction:new{end0=false, end1=true, beta=1.1},
      north=RobertsFunction:new{end0=false, end1=true, beta=1.1},
      west=GeometricFunction:new{a=mesh.wall_first_cell_m/r_inlet, r=growth, N=nj_core+1, reverse=true},
      east=GeometricFunction:new{a=mesh.wall_first_cell_m/r_throat, r=growth, N=nj_core+1, reverse=true}
   }
   cf_divergent = {
      south=RobertsFunction:new{end0=true, end1=true, beta=1.1},
      north=RobertsFunction:new{end0=true, end1=true, beta=1.1},
      west=GeometricFunction:new{a=mesh.wall_first_cell_m/r_throat, r=growth, N=nj_core+1, reverse=true},
      east=GeometricFunction:new{a=mesh.wall_first_cell_m/r_exit, r=growth, N=nj_core+1, reverse=true}
   }
   cf_external = {
      west=GeometricFunction:new{a=mesh.wall_first_cell_m/r_exit, r=growth, N=nj_core+1, reverse=true},
      east=GeometricFunction:new{a=mesh.wall_first_cell_m/r_exit, r=growth, N=nj_core+1, reverse=true}
   }
end
local grids = {
   StructuredGrid:new{psurface=patches[1], niv=ni_convergent+1, njv=nj_core+1, cfList=cf_convergent},
   StructuredGrid:new{psurface=patches[2], niv=ni_divergent+1, njv=nj_core+1, cfList=cf_divergent},
   StructuredGrid:new{psurface=patches[3], niv=ni_external+1, njv=nj_core+1, cfList=cf_external},
   StructuredGrid:new{psurface=patches[4], niv=ni_external+1, njv=nj_outer+1}
}

local initial_tag = screen.initial_solution_dir and 'initial' or nil
local reservoir_tag = initial_tag or 'reservoir'
local ambient_tag = initial_tag or 'ambient'

registerFluidGridArray{
   grid=grids[1], nib=1, njb=1, fsTag=reservoir_tag,
   bcTags={west='inlet', north='wall'}
}
registerFluidGridArray{
   grid=grids[2], nib=2, njb=1, fsTag=reservoir_tag,
   bcTags={north='wall'}
}
registerFluidGridArray{
   grid=grids[3], nib=3, njb=1, fsTag=ambient_tag,
   bcTags={east='outflow'}
}
registerFluidGridArray{
   grid=grids[4], nib=3, njb=1, fsTag=ambient_tag,
   bcTags={west='wall', north='ambient', east='outflow'}
}
identifyGridConnections()

local cells = (ni_convergent + ni_divergent + ni_external)*nj_core + ni_external*nj_outer
print(string.format('External grid %s: %d cells in 9 blocks', mesh.level, cells))
if mesh.wall_first_cell_m then
   print(string.format('Requested wall-normal first cell: %.9g m', mesh.wall_first_cell_m))
end
