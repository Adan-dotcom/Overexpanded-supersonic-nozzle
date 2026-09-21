print('DLR-PAR cold-N2 three-level screening grid')

config.dimensions = 2
config.axisymmetric = true

local levels = {
   coarse = {ni_convergent=90,  ni_divergent=450, nj=96},
   medium = {ni_convergent=120, ni_divergent=600, nj=144},
   fine   = {ni_convergent=180, ni_divergent=900, nj=192}
}
local level_name = os.getenv('DLR_MESH_LEVEL') or 'medium'
local level = levels[level_name]
if level == nil then
   error('DLR_MESH_LEVEL must be coarse, medium or fine')
end

local x_inlet, x_throat, x_exit = -0.02268, 0.0, 0.12502
local r_inlet, r_throat, r_exit = 0.020, 0.010, 0.05477226

-- The runner conditions these path files to uniform x spacing because
-- Spline2 follows their source-point parameterization.
local wall_convergent = Spline2:new{filename='convergent.txt'}
local wall_divergent = Spline2:new{filename='divergent.txt'}
local axis_convergent = Line:new{
   p0={x=x_inlet, y=0.0}, p1={x=x_throat, y=0.0}
}
local axis_divergent = Line:new{
   p0={x=x_throat, y=0.0}, p1={x=x_exit, y=0.0}
}
local inlet = Line:new{
   p0={x=x_inlet, y=0.0}, p1={x=x_inlet, y=r_inlet}
}
local throat = Line:new{
   p0={x=x_throat, y=0.0}, p1={x=x_throat, y=r_throat}
}
local exit = Line:new{
   p0={x=x_exit, y=0.0}, p1={x=x_exit, y=r_exit}
}

local patch_convergent = CoonsPatch:new{
   north=wall_convergent, east=throat,
   south=axis_convergent, west=inlet
}
local patch_divergent = CoonsPatch:new{
   north=wall_divergent, east=exit,
   south=axis_divergent, west=throat
}

local cluster_to_throat_upstream = RobertsFunction:new{
   end0=false, end1=true, beta=1.1
}
local cluster_to_throat_downstream = RobertsFunction:new{
   end0=true, end1=false, beta=1.1
}
-- The same wall-normal mapping is used on all levels so refinement reduces
-- the first-cell height monotonically. Actual y+ remains a flow-screen output.
local cluster_to_wall = RobertsFunction:new{
   end0=false, end1=true, beta=1.03
}

local grid_convergent = StructuredGrid:new{
   psurface=patch_convergent,
   niv=level.ni_convergent+1,
   njv=level.nj+1,
   cfList={
      north=cluster_to_throat_upstream,
      south=cluster_to_throat_upstream,
      east=cluster_to_wall,
      west=cluster_to_wall
   }
}
local grid_divergent = StructuredGrid:new{
   psurface=patch_divergent,
   niv=level.ni_divergent+1,
   njv=level.nj+1,
   cfList={
      north=cluster_to_throat_downstream,
      south=cluster_to_throat_downstream,
      east=cluster_to_wall,
      west=cluster_to_wall
   }
}

registerFluidGridArray{
   grid=grid_convergent, nib=1, njb=1, fsTag='initial',
   bcTags={west='inlet', north='wall'}
}
registerFluidGridArray{
   grid=grid_divergent, nib=5, njb=1, fsTag='initial',
   bcTags={east='outlet', north='wall'}
}
identifyGridConnections()

local cells = (level.ni_convergent+level.ni_divergent)*level.nj
print(string.format('Mesh level=%s cells=%d blocks=6', level_name, cells))
