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

## Transfer slab load to beams

1. Reuse the accepted HW1 slab polygon and openings.
2. Define finite beam segments between every adjacent structural grid point.
3. Assign each loaded slab cell to its nearest beam segment. Parallel edges divide at mid-lines; perpendicular edges divide on 45-degree bisectors.
4. Bin assigned area along each beam to retain triangular, trapezoidal and superposed line-load shapes.
5. Store dead and live profiles separately. Compute an equivalent UDL only as total load divided by span, and do not use it as a local shear substitute.
6. Confirm the sum of all beam tributary areas and beam loads closes to the reused HW1 slab area and floor load.

## Build and check an OpenSees beam/subframe pair

1. Write and preserve a plain-language briefing before code generation.
2. Establish qL2/8 and qL2/12 moment scales and a qualitative curvature sketch before solving.
3. For the standalone beam, use continuous beam nodes with vertical support restraints and free rotations.
4. For the one-floor subframe, replace point supports by 3 m elastic columns with fixed bases and shared beam-column nodes.
5. Apply the frozen piecewise line-load profile in local negative y, solve, then recover N, V and M from element end forces and equilibrium.
6. Require reaction/load closure, sagging-positive and hogging-negative regions, and a peak moment inside the pre-solve envelope.
7. Compare subframe column-top axial forces with HW1 one-floor axial estimates without tuning either model; explain differences in model scope and load path.

