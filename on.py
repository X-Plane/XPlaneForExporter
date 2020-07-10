import argparse
import os
import sys

import bpy

try:
    from io_xplane2blender.xplane_249_converter.xplane_249_constants import ProjectType
except:
    pass

# from io_xplane2blender.xplane_249_converter.xplane_249_constants import WorkflowType
# We can tell if we're launched with Blender or with CLI from sys.argv?
def _make_argparser():
    parser = argparse.ArgumentParser(
        description="Our custom Blender launcher. A workflow booster!",
        epilog="Invoke as Blender my_file.blend -P on_start.py -- -e",
    )

    parser.add_argument(
        "-c",
        "--convert",
        help="Run the 2.49 converter (runs before anything else)",
        default="",
        nargs="?",
        choices={"BULK", "REGULAR"},
    )

    parser.add_argument(
        "--project-type",
        help="What project type to give to the converter",
        default="AIRCRAFT",
        nargs="?",
        choices={"AIRCRAFT", "SCENERY"},
    )

    parser.add_argument(
        "-e",
        "--export",
        help="Runs the exporter after loading given file (and any conversion)",
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "-l",
        "--use-last",
        help="Uses the most recently used file",
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "-s",
        "--stay-open",
        help="Keep GUI open after running commands",
        default=False,
        action="store_true",
    )

    return parser


def main(argv=None) -> int:
    """
    Return is exit code, 0 for good, anything else is an error
    """

    """
    for obj in bpy.data.objects:
        try:
            print(obj.bl_rna.properties["name"].name)

            print(obj.name)
        except UnicodeDecodeError:
            print("ran into trouble")
    """

    exit_code = 0
    if argv is None:
        import sys

        if "--" in sys.argv:
            argv = _make_argparser().parse_args(sys.argv[sys.argv.index("--") + 1 :])
        else:
            argv = _make_argparser().parse_args("")

    def quit():
        if not argv.stay_open:
            bpy.ops.wm.quit_blender()

    if argv.use_last:
        with open(
            os.path.join(bpy.utils.user_resource("CONFIG"), "recent-files.txt")
        ) as recent_files:
            try:
                bpy.ops.wm.open_mainfile(
                    filepath="{}".format(recent_files.readline().rstrip())
                )
            except RuntimeError as e:  # File not found
                print(e)
                quit()

    if argv.convert:
        try:
            bpy.ops.xplane.do_249_conversion(
                project_type=argv.project_type, workflow_type=argv.convert
            )
        except Exception as e:
            print("grrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr", e)
            pass
            # print("onstart", e)
            # bpy.ops.xplane.do_249_conversion(workflow_type=argv.convert)
    if argv.export:
        bpy.ops.export.xplane_for()

    quit()


if __name__ == "__main__":
    main()
