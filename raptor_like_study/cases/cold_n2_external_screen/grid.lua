print('DLR-PAR cold-N2 external-plume screening grid')

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

-- Screening resolution only; this is not a validation or wall-resolution mesh.
local ni_convergent, ni_divergent, ni_external = 32, 128, 160
local nj_core, nj_outer = 48, 48
local grids = {
   StructuredGrid:new{psurface=patches[1], niv=ni_convergent+1, njv=nj_core+1},
   StructuredGrid:new{psurface=patches[2], niv=ni_divergent+1, njv=nj_core+1},
   StructuredGrid:new{psurface=patches[3], niv=ni_external+1, njv=nj_core+1},
   StructuredGrid:new{psurface=patches[4], niv=ni_external+1, njv=nj_outer+1}
}

registerFluidGridArray{
   grid=grids[1], nib=1, njb=1, fsTag='reservoir',
   bcTags={west='inlet', north='wall'}
}
registerFluidGridArray{
   grid=grids[2], nib=2, njb=1, fsTag='reservoir',
   bcTags={north='wall'}
}
registerFluidGridArray{
   grid=grids[3], nib=3, njb=1, fsTag='ambient',
   bcTags={east='outflow'}
}
registerFluidGridArray{
   grid=grids[4], nib=3, njb=1, fsTag='ambient',
   bcTags={west='wall', north='ambient', east='outflow'}
}
identifyGridConnections()

local cells = (ni_convergent + ni_divergent + 2*ni_external)*nj_core
print(string.format('External screening grid: %d cells in 9 blocks', cells))
