"""
block_with_boss.py — a minimal end-to-end headless NX journal.

Builds an 80x60x30 block with a Ø20x25 boss, blends and chamfers an edge,
assigns Steel, measures mass properties, and exports STEP AP242.

It is assembled entirely from the verified recipes in ../docs. Treat it as a
readable template to adapt, not a turnkey tool — signatures are NX 2506; check
yours against your local stubs (see docs/06-resources.md).

Run (PowerShell):
    $env:UGII_ROOT_DIR = "C:\\Program Files\\Siemens\\NX2506\\NXBIN"
    & "$env:UGII_ROOT_DIR\\run_journal.exe" block_with_boss.py -args out.prt

The single trailing arg is the output .prt path.
"""

# NOTE: keep all submodule imports at MODULE TOP. Importing NXOpen.<X> inside a
# function makes `NXOpen` a function-local name -> "cannot access local variable".
import sys
import os
import math
import NXOpen
import NXOpen.Features
import NXOpen.GeometricUtilities


def _mm(part, name, value):
    """Create a millimetre expression and return it."""
    unit = part.UnitCollection.FindObject("MilliMeter")
    return part.Expressions.CreateWithUnits(f"{name}={value}", unit)


def main():
    out_prt = sys.argv[1] if len(sys.argv) > 1 else "block_with_boss.prt"
    out_prt = os.path.abspath(out_prt)

    # NewBaseDisplay refuses to overwrite — clear the target first.
    if os.path.exists(out_prt):
        os.remove(out_prt)

    session = NXOpen.Session.GetSession()
    part = session.Parts.NewBaseDisplay(out_prt, NXOpen.BasePart.Units.Millimeters)
    if isinstance(part, tuple):          # some paths return (part, status)
        part = part[0]

    upd = session.UpdateManager

    # ------------------------------------------------------------------ block
    mark = session.SetUndoMark(NXOpen.Session.MarkVisibility.Visible, "block")
    block_builder = part.Features.CreateBlockFeatureBuilder(NXOpen.Features.Feature.Null)
    block_builder.Type = NXOpen.Features.BlockFeatureBuilder.Types.OriginAndEdgeLengths
    block_builder.SetOriginAndLengths(
        NXOpen.Point3d(0.0, 0.0, 0.0), "80", "60", "30")   # lengths are strings
    block_builder.SetBooleanOperationAndTarget(
        NXOpen.Features.Feature.BooleanType.Create, NXOpen.Body.Null)
    block_feat = block_builder.CommitFeature()
    block_builder.Destroy()
    upd.DoUpdate(mark)                                       # REQUIRED after every feature

    block_body = block_feat.GetBodies()[0]
    block_body.SetName("Base_Block")

    # ------------------------------------------------------------------- boss
    # Ø20 x 25 cylinder centred on the top face, united into the block.
    mark = session.SetUndoMark(NXOpen.Session.MarkVisibility.Visible, "boss")
    cyl = part.Features.CreateCylinderBuilder(NXOpen.Features.Feature.Null)
    cyl.Type = NXOpen.Features.CylinderBuilder.Types.AxisDiameterAndHeight
    origin = part.Points.CreatePoint(NXOpen.Point3d(40.0, 30.0, 30.0))
    zdir = part.Directions.CreateDirection(
        NXOpen.Point3d(40.0, 30.0, 30.0), NXOpen.Vector3d(0.0, 0.0, 1.0),
        NXOpen.SmartObject.UpdateOption.WithinModeling)
    cyl.Axis = part.Axes.CreateAxis(origin, zdir, NXOpen.SmartObject.UpdateOption.WithinModeling)
    cyl.Diameter.RightHandSide = "20"
    cyl.Height.RightHandSide = "25"
    cyl.BooleanOption.Type = NXOpen.GeometricUtilities.BooleanOperation.BooleanType.Unite
    cyl.BooleanOption.SetTargetBodies([block_body])
    cyl.CommitFeature()
    cyl.Destroy()
    upd.DoUpdate(mark)

    # ------------------------------------------------------- edge blend (r=4)
    # Pick a vertical edge of the block to blend. (In real code, filter edges by
    # geometry rather than index — indices are not stable across rebuilds.)
    mark = session.SetUndoMark(NXOpen.Session.MarkVisibility.Visible, "blend")
    edges = [e for e in block_body.GetEdges()]
    if edges:
        ebb = part.Features.CreateEdgeBlendBuilder(NXOpen.Features.Feature.Null)
        col = part.ScCollectors.CreateCollector()
        col.ReplaceRules([part.ScRuleFactory.CreateRuleEdgeDumb([edges[0]])], False)
        ebb.AddChainset(col, "4")                          # radius is a STRING
        ebb.CommitFeature()
        ebb.Destroy()
        upd.DoUpdate(mark)

    # --------------------------------------------------------------- material
    mark = session.SetUndoMark(NXOpen.Session.MarkVisibility.Visible, "material")
    pm = part.MaterialManager.PhysicalMaterials
    steel = pm.LoadFromNxmatmllibrary("Steel")
    steel.AssignObjects([block_body])
    upd.DoUpdate(mark)

    # -------------------------------------------------------- mass properties
    uc = part.UnitCollection
    units = [uc.FindObject(n) for n in
             ("SquareMilliMeter", "CubicMilliMeter", "Kilogram", "MilliMeter", "Newton")]
    mp = part.MeasureManager.NewMassProperties(units, 0.99, [block_body])
    print(f"volume = {mp.Volume:.2f} mm^3   area = {mp.Area:.2f} mm^2   mass = {mp.Mass:.4f} kg")

    # ------------------------------------------------------------ STEP export
    stp = os.path.splitext(out_prt)[0] + ".stp"
    sc = session.DexManager.CreateStepCreator()
    sc.ExportAs = NXOpen.StepCreator.ExportAsOption.Ap242
    sc.ObjectTypes.Solids = True
    sc.ExportSelectionBlock.SelectionScope = NXOpen.ObjectSelector.Scope.SelectedObjects
    sc.ExportSelectionBlock.SelectionComp.Add([block_body])   # solids only
    sc.InputFile = part.FullPath
    sc.OutputFile = stp
    sc.Commit()
    sc.Destroy()

    part.Save(NXOpen.BasePart.SaveComponents.TrueValue, NXOpen.BasePart.CloseAfterSave.FalseValue)
    print(f"done -> {out_prt}  +  {stp}")


if __name__ == "__main__":
    main()
