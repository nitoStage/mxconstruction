# Palvic residence: The Pointe at Jackson Hill, Lot 7 (3D model)

A Blender model built from the Drafting Designs LLC sheets 1–3 (Feb 05, 2024).
Units are imperial: the scene is set to feet/inches, and every dimension in the script is in feet.

| File | What it is |
|---|---|
| `build_palvic_house.py` | Generator script. Contains all measured plan data and builds the whole model |
| `palvic_lot7.blend` | The generated model, ready to open |
| `palvic_lot7.glb` | The same model as glTF (SketchUp, Unreal, three.js, etc.) |
| `render_views.py` | Renders the preview images below |
| `renders/` | Front, back, interior and top-down cutaway renders |

## Using it in your own Blender 5.x file

1. Open the **Scripting** workspace, then **Open** `build_palvic_house.py`, then **Run Script**.
2. The script builds everything inside the collection **"Palvic House - Lot 7"**. Running it again replaces only
   that collection, so the rest of your file is left alone.
3. The scene switches to Imperial units in feet, and the N-panel shows dimensions such as `9' 0"`.

Headless: `blender -b -P build_palvic_house.py -- --save palvic_lot7.blend --glb palvic_lot7.glb`

## What is modeled

- **Walls.** The stud footprints come straight from the vector floor plan: 3½" studs, ½" drywall, lap siding outside.
  The front walls have a stone wainscot at 4'-10" with a cap. Corner boards are included, and there are baseboards in every room.
- **Doors (18).** Each door has its plan size (2'0", 2'8", 3'0"), jambs, casing on both sides, and a closed leaf.
  Exterior doors are 6-panel, the front door has a full glass lite, and there is a 4'-6" cased opening at the hall.
- **Windows (8, plus 3 in the dormer).** Every mulled unit from the plan is included: 3060, 2-3060, 3-2040, 2-2060 and 2-2630.
  All heads are at 7'-8". Each window has a black frame, a meeting rail, colonial grilles, exterior casing with sill and drip cap,
  and an interior stool with apron.
- **Kitchen.** Base and upper cabinets, granite tops, the sink under the 3-2040 window, a dishwasher,
  a 30" electric range with hood, the refrigerator, and the 4'×7' island with pendants and stools.
- **Baths.**
  - Master: double vanity, linen tower, freestanding tub, a 3'-0" glass shower, and a separate WC.
  - Hall: tub with tile surround, vanity, toilet and linen.
  - Half bath: toilet and vanity.
- **Utility, mud hall and closets.** Washer and electric dryer, utility sink, tall cabinet, and lockers with a bench.
  All closets have shelf and rod, and the carport storage room has shelving.
- **Fireplace.** Wood-burning firebox with a stone surround, raised hearth and mantel. The chimney chase above has siding, a cap and two flues.
- **Porches and carport.**
  - Front porch: 8' deep, with 8×8 columns on stone pedestals.
  - Back porch and patio: 6×6 posts.
  - Carport: 804 sq ft with a 56 sq ft storage room and a half bath.
  - All slabs match the plan areas.
- **Roof.**
  - Main roof: 5:12 gable with its ridge running east–west.
  - Carport: separate 5:12 gable.
  - 2:12 standing-seam shed dormer with six 2630 clerestory windows.
  - Also included: fascia, soffits, gutters and gable vents.
- **Extras.** Ceiling fans and a chandelier, following the electrical plan. There are also point lights for interior renders,
  room labels (hidden in renders), and site work (lawn, driveway, front walk).

Each group is in its own numbered collection (Walls, Doors, Windows, Roof, Ceilings…), so you can hide the roof and ceilings for a cutaway.

## Assumptions: please verify

- The roof plan is marked *not to scale*. The ridge position, the 1'-3" overhangs and the 9'-6" roof bearing height were derived from the
  1/4" elevations (ridge at about 22'). The shed dormer's depth and where it meets the main roof come from the front and side elevations.
- The drawings don't specify finishes, so these are placeholders:
  - wood floor in living areas, tile in baths and utility, carpet in bedrooms;
  - white cabinets and dark granite;
  - siding color.
- The narrow closet between the living room and the master vanity has no door on the plan, so it is left enclosed.
- Outlets and switches from the electrical plan are not modeled. Furniture is not included because it isn't on the plans.
