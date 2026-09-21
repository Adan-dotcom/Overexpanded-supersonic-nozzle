print('DLR-PAR axisymmetric geometry-only inspection grid')

config.dimensions = 2
config.axisymmetric = true

local x_inlet, x_throat, x_exit = -0.02268, 0.0, 0.12502
local r_inlet, r_throat, r_exit = 0.020, 0.010, 0.05477226

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
local cluster_to_wall = RobertsFunction:new{
   end0=false, end1=true, beta=1.05
}

local ni_convergent, ni_divergent, nj = 120, 600, 128
local grid_convergent = StructuredGrid:new{
   psurface=patch_convergent,
   niv=ni_convergent+1,
   njv=nj+1,
   cfList={
      north=cluster_to_throat_upstream,
      south=cluster_to_throat_upstream,
      east=cluster_to_wall,
      west=cluster_to_wall
   }
}
local grid_divergent = StructuredGrid:new{
   psurface=patch_divergent,
   niv=ni_divergent+1,
   njv=nj+1,
   cfList={
      north=cluster_to_throat_downstream,
      south=cluster_to_throat_downstream,
      east=cluster_to_wall,
      west=cluster_to_wall
   }
}

registerFluidGridArray{
   grid=grid_convergent, nib=1, njb=1, fsTag='geometry_only',
   bcTags={west='inlet', north='wall'}
}
registerFluidGridArray{
   grid=grid_divergent, nib=5, njb=1, fsTag='geometry_only',
   bcTags={east='exit', north='wall'}
}
identifyGridConnections()

print(string.format('Inspection grid: %d cells in 6 blocks',
                    (ni_convergent+ni_divergent)*nj))

