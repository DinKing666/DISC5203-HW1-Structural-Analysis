# Reusable HW2 procedures

## Transfer slab load to beams

1. Load the accepted HW1 slab polygon and openings from `../HW1/`.
2. Define finite beam segments between adjacent structural grid points.
3. Classify each panel edge before assigning cells: exterior main-slab edges are discontinuous/simple, shared interior grid edges are continuous/fixed, and balcony free edges are not supports.
4. Use equal edge weights for matched supports, giving 45-degree corner boundaries. For a mixed continuous/discontinuous corner, use a continuous-edge attraction weight of sqrt(3), giving 60 degrees from the continuous edge and 30 degrees from the discontinuous edge.
5. Assign each cantilever balcony entirely to its single support line, then bin all assigned area along each beam to retain polygonal, cantilever-uniform, and superposed profiles.
6. Store dead and live profiles separately. Compute both the total-load-equivalent UDL and the simply-supported midspan-moment-equivalent UDL.
7. Confirm that all beam tributary areas and loads close to the reused HW1 slab totals.

## Build and check an OpenSees model pair

1. Preserve a plain-language structural briefing before generating code.
2. Establish qL2/8 and qL2/12 moment scales and a qualitative curvature sketch before solving.
3. Model the standalone beam with continuous nodes, vertical support restraints, and free rotations.
4. Replace point supports by 3 m fixed-base elastic columns for the one-floor subframe.
5. Apply the same frozen local-negative-y load profile to both models.
6. Require reaction/load closure, sagging-positive and hogging-negative regions, and peak moments inside the pre-solve envelope.
7. Compare subframe column-top axial forces with the unchanged HW1 one-floor estimates and explain model-scope differences without tuning either result.
