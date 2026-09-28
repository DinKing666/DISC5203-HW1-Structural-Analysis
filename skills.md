# Reusable procedures

## Digitize a floor plan

1. Select two or more printed dimensions for scale and consistency checks.
2. Adopt a visible structural grid intersection as the local datum.
3. Record the slab boundary, excluded openings, columns, and wall centreline segments in a JSON configuration file.
4. Overlay the digitized geometry on a clean plot and review every support ID.
5. Record ambiguous details explicitly as assumptions.

## Compute tributary areas

1. Discretize the net slab into square cells of the configured resolution.
2. Measure rectilinear (L1) distance from each cell centre to every column point and every axis-aligned wall centreline segment.
3. Assign the cell to the nearest vertical element; resolve exact ties deterministically by element ID.
4. Confirm that parallel supports have straight mid-span boundaries and perpendicular wall corners have 45-degree divisions.
5. Sum cell areas by support and compare their total with the independently computed polygon area.
6. Refine the grid until the closure error is below the stated tolerance.

## Compute gravity loads

1. Calculate slab self-weight as concrete unit weight times slab thickness.
2. Multiply tributary area by dead and live area loads separately.
3. Add them for one-floor axial load.
4. For identical stacked floors, multiply one-floor values by the number of floors to obtain base cumulative load.
5. Verify global load conservation independently from the element table.

