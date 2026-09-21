print('Products/air compressible mixing benchmark: build the six-block grid.')

config.dimensions = 2
config.axisymmetric = false

-- Rectangular planar mixing layer.  Two grid arrays let the west boundary carry
-- distinct product and air tags while the common y=0 face remains connected.
local xmin, xmax = 0.0, 0.120
local ymin, ymid, ymax = -0.020, 0.0, 0.020
local nic, njc_half = 180, 100

local lower = CoonsPatch:new{
   p00={x=xmin, y=ymin}, p10={x=xmax, y=ymin},
   p01={x=xmin, y=ymid}, p11={x=xmax, y=ymid}
}
local upper = CoonsPatch:new{
   p00={x=xmin, y=ymid}, p10={x=xmax, y=ymid},
   p01={x=xmin, y=ymax}, p11={x=xmax, y=ymax}
}

local lower_grid = StructuredGrid:new{
   psurface=lower, niv=nic+1, njv=njc_half+1
}
local upper_grid = StructuredGrid:new{
   psurface=upper, niv=nic+1, njv=njc_half+1
}

registerFluidGridArray{
   grid=lower_grid, nib=3, njb=1, fsTag='air',
   bcTags={west='air_inflow', east='outflow', south='slip_wall'}
}
registerFluidGridArray{
   grid=upper_grid, nib=3, njb=1, fsTag='products',
   bcTags={west='products_inflow', east='outflow', north='slip_wall'}
}
identifyGridConnections()

print(string.format('Grid cells: %d; blocks: 6; cells/block: %d',
                    nic*(2*njc_half), (nic/3)*njc_half))
