import collections
import itertools
import os
import pathlib
import shutil
import sys
import unittest
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import bpy

import io_scene_xplane_for
from io_scene_xplane_for import forest_file, forest_helpers, forest_logger

print(forest_helpers.get_layer_collections_in_view_layer)
from io_scene_xplane_for.forest_logger import ForestLogger, logger
from . import test_creation_helpers

FLOAT_TOLERANCE = 0.0001

__dirname__ = os.path.dirname(__file__)

FilterLinesCallback = Callable[[List[Union[float, str]]], bool]


class TemporarilyMakeRootExportable:
    """
    Ensures a potential_root will be exportable
    and when finished, will revert it's exportable
    and viewport settings
    """

    def __init__(
        self,
        potential_root: Union[forest_helpers.PotentialRoot, str],
        view_layer: Optional[bpy.types.ViewLayer] = None,
    ):
        """
        If view_layer is None, uses current scene's 1st view_layer
        """
        self.view_layer = view_layer or bpy.context.scene.view_layers[0]

        if isinstance(potential_root, str):
            self.potential_root = test_creation_helpers.lookup_potential_root_from_name(
                potential_root
            )
        else:
            self.potential_root = potential_root

        all_layer_collections = {
            lc.name: lc
            for lc in io_scene_xplane_for.forest_helpers.get_layer_collections_in_view_layer(
                self.view_layer
            )
        }
        self.original_hide_viewport = all_layer_collections[
            self.potential_root.name
        ].hide_viewport

        self.original_disable_viewport = self.potential_root.hide_viewport

    def __enter__(self):
        test_creation_helpers.make_root_exportable(self.potential_root, self.view_layer)

    def __exit__(self, exc_type, value, traceback):
        test_creation_helpers.make_root_unexportable(
            self.potential_root,
            self.view_layer,
            self.original_hide_viewport,
            self.original_disable_viewport,
        )


class ForestTestCase(unittest.TestCase):
    def setUp(self, useLogger=True):
        dd_index = sys.argv.index("--")
        blender_args, xplane_args = sys.argv[:dd_index], sys.argv[dd_index + 1 :]
        # setDebug('--force-xplane-debug' in xplane_args)

        # if useLogger:
        #    self.useLogger()

        # logger.warn("---------------")

    def useLogger(self):
        # TODO if debug
        logger.reset()

    def assertFloatsEqual(self, a: float, b: float, tolerance: float = FLOAT_TOLERANCE):
        """
        Tests if floats are equal, with a default tollerance. The difference between this and assertAlmostEqual
        is that we use abs instead of round, then compare
        """
        if abs(a - b) < tolerance:
            return True
        else:
            raise AssertionError(f"{a} != {b}, within a tolerance of {tolerance}")

    def assertFloatVectorsEqual(
        self, a: int, b: int, tolerance: float = FLOAT_TOLERANCE
    ):
        self.assertEquals(len(a), len(b))
        for a_comp, b_comp in zip(a, b):
            self.assertFloatsEqual(a_comp, b_comp, tolerance)

    def assertLoggerErrors(
        self, expected_logger_codes=List[forest_logger.MessageCodes]
    ) -> None:
        """
        Asserts logger has same error codes,
        encountered in the same order, as the test wants
        """
        try:
            self.assertEqual(
                [m.msg_code for m in logger.messages], expected_logger_codes
            )
        except AssertionError as e:
            raise AssertionError(
                f"Expected {expected_logger_codes} logger errors, got {[m.msg_code for m in logger.messages]}"
            ) from None
        else:
            logger.clearMessages()

    def assertMatricesEqual(self, mA, mB, tolerance=FLOAT_TOLERANCE):
        for row_a, row_b in zip(mA, mB):
            self.assertFloatVectorsEqual(row_a, row_b, tolerance)

    def parseFileToLines(self, data: str) -> List[Union[float, str]]:
        """
        Turns a string of \n seperated lines into a List[Union[float,str]]
        without comments or 0 length strings. All numeric parts are converted
        """
        lines: Dict[int, Union[float, str]] = {}

        def tryToFloat(part: str) -> Union[float, str]:
            try:
                return float(part)
            except (TypeError, ValueError):
                return part

        for i, line in enumerate(data.split("\n"), start=1):
            if "#" in line:
                line = line[0 : line.index("#")]
            line = line.strip()
            if line:
                if line.startswith("800"):
                    lines[i] = line.split()
                else:
                    lines[i] = tuple(map(tryToFloat, line.split()))

        return lines

    def assertFilesEqual(
        self,
        a: str,
        b: str,
        filterCallback: Union[FilterLinesCallback, List[str]],
        floatTolerance: float = FLOAT_TOLERANCE,
    ):
        """
        a and b should be the contents of files a and b as returned
        from open(file).readlines().

        By convention, a is usually the export output, b is usually the fixture file
        """

        def isnumber(d):
            return isinstance(d, (float, int))

        linesA = self.parseFileToLines(a).values()
        linesB = self.parseFileToLines(b).values()

        if isinstance(filterCallback, collections.abc.Collection):
            linesA = [
                line
                for line in linesA
                if any(directive in line[0] for directive in filterCallback)
            ]
            linesB = [
                line
                for line in linesB
                if any(directive in line[0] for directive in filterCallback)
            ]
        else:
            linesA = list(filter(filterCallback, linesA))
            linesB = list(filter(filterCallback, linesB))

        # ensure same number of lines
        try:
            self.assertEquals(len(linesA), len(linesB))
        except AssertionError as e:
            # TODO: Incorporate line numbers
            only_in_a = set(linesA) - set(linesB)
            only_in_b = set(linesB) - set(linesA)
            diff = ">" + "\n>".join(
                " ".join(map(str, l))
                for l in (only_in_a if len(only_in_a) > len(only_in_b) else only_in_b)
            )
            diff += "\n\n>" + "\n>".join(
                " ".join(map(str, l))
                for l in (only_in_a if len(only_in_a) < len(only_in_b) else only_in_b)
            )

            raise AssertionError(
                f"Length of filtered parsed lines unequal: " f"{e.args[0]}\n{diff}\n"
            ) from None

        for lineIndex, (lineA, lineB) in enumerate(zip(linesA, linesB)):
            try:
                # print(f"lineA:{lineA}, lineB:{lineB}")
                self.assertEquals(len(lineA), len(lineB))
            except AssertionError as e:
                raise AssertionError(
                    f"Number of line components unequal: {e.args[0]}\n"
                    f"{lineIndex}> {lineA} ({len(lineA)})\n"
                    f"{lineIndex}> {lineB} ({len(lineB)})"
                ) from None

            for linePos, (segmentA, segmentB) in enumerate(zip(lineA, lineB)):
                # assure same values (floats must be compared with tolerance)
                if isnumber(segmentA) and isnumber(segmentB):
                    # TODO: This is too simple! This will make call abs on the <value> AND <angle> in ANIM_rotate_key
                    # which are not semantically the same!
                    # Also not covered are PHI, PSI, and THETA!
                    segmentA = (
                        abs(segmentA)
                        if "rotate" in lineA[0] or "manip_keyframe" in lineA[0]
                        else segmentA
                    )
                    segmentB = (
                        abs(segmentB)
                        if "rotate" in lineB[0] or "manip_keyframe" in lineB[0]
                        else segmentB
                    )
                    try:
                        self.assertFloatsEqual(segmentA, segmentB, floatTolerance)
                    except AssertionError as e:

                        def make_context(source: List[str], segment: str) -> str:
                            current_line = (
                                f"{lineIndex}> {' '.join(map(str, source[lineIndex]))}"
                            )
                            # Makes something like
                            # 480> ATTR_ -0.45643 1.0 sim/test1
                            # ?          ^~~~~~~~
                            # 480> ATTR_ -1.0 1.0 sim/test1
                            # ?          ^~~~
                            question_line = (
                                "?"
                                + " " * (len(str(lineIndex)) + 3)
                                + "^".rjust(
                                    len(" ".join(map(str, lineA[:linePos]))), " "
                                )
                                + "~" * (len(str(segment)) - 1)
                            )

                            return "\n".join(
                                (
                                    f"{lineIndex - 1}: {' '.join(map(str, source[lineIndex-1]))}"
                                    if lineIndex > 0
                                    else "",
                                    current_line,
                                    question_line,
                                    f"{lineIndex + 1}: {' '.join(map(str, source[lineIndex+1]))}"
                                    if lineIndex + 1 < len(source)
                                    else "",
                                )
                            )

                        context_lineA = make_context(linesA, segmentA)
                        context_lineB = make_context(linesB, segmentB)

                        raise AssertionError(
                            e.args[0]
                            + "\n"
                            + "\n\n".join((context_lineA, context_lineB))
                        ) from None
                else:
                    self.assertEquals(segmentA, segmentB)

    def assertFileOutputEqualsFixture(
        self,
        fileOutput: str,
        fixturePath: str,
        filterCallback: Union[FilterLinesCallback, List[str]],
        floatTolerance: float = FLOAT_TOLERANCE,
    ) -> None:
        """
        Compares the output of ForestFile.write (a \n separated str) to a fixture on disk.

        A filterCallback ensures only matching lines are compared.
        Highly recommended, with as simple a function as possible to prevent fixture fragility.
        """

        with open(fixturePath, "r") as fixtureFile:
            fixtureOutput = fixtureFile.read()

        return self.assertFilesEqual(
            fileOutput, fixtureOutput, filterCallback, floatTolerance
        )

    def assertFileTmpEqualsFixture(
        self,
        tmpPath: str,
        fixturePath: str,
        filterCallback: Union[FilterLinesCallback, List[str]],
        floatTolerance: float = FLOAT_TOLERANCE,
    ):
        tmpFile = open(tmpPath, "r")
        tmpOutput = tmpFile.read()
        tmpFile.close()

        return self.assertFileOutputEqualsFixture(
            tmpOutput, fixturePath, filterCallback, floatTolerance
        )

    def assertExportableRootExportEqualsFixture(
        self,
        root_object: Union[bpy.types.Collection, bpy.types.Object, str],
        fixturePath: str,
        filterCallback: [Union[FilterLinesCallback, List[str]]],
        tmpFilename: Optional[str] = None,
        floatTolerance: float = FLOAT_TOLERANCE,
    ) -> None:
        """
        Exports only a specific exportable root and compares the output
        to a fixutre.

        If filterCallback is a List[str], those directives will be filtered
        will be used. Tip: Use TRIS or POINT_COUNTS instead of VT.
        """
        out = self.exportExportableRoot(root_object, tmpFilename)
        self.assertFileOutputEqualsFixture(
            out, fixturePath, filterCallback, floatTolerance
        )

    def createForestFileFromPotentialRoot(
        self,
        potential_root: Union[forest_helpers.PotentialRoot, str],
        view_layer: Optional[bpy.types.ViewLayer] = None,
    ) -> forest_file.ForestFile:
        """
        A thin wrapper around forest_file.create_forest_single_file where the potential root
        is temporarily is made exportable.
        """
        potential_root = (
            test_creation_helpers.lookup_potential_root_from_name(potential_root)
            if isinstance(potential_root, str)
            else potential_root
        )

        view_layer = view_layer or bpy.context.scene.view_layers[0]
        with TemporarilyMakeRootExportable(potential_root, view_layer):
            xp_file = forest_file.create_forest_single_file(potential_root)
        return xp_file

    def exportExportableRoot(
        self,
        potential_root: Union[forest_helpers.PotentialRoot, str],
        dest: Optional[str] = None,
        force_visible=True,
        view_layer: Optional[bpy.types.ViewLayer] = None,
    ) -> str:
        """
        Returns the result of calling xplaneFile.write()

        - dest is a filepath without the file extension .obj, writes result to the tmp folder if not None
        - force_visible forces a potential_root to be visible
        - view_layer is needed for checking if potential_root is visible, when None
          the current scene's 1st view layer is used

        If an ForestFile could not be made, a ValueError will bubble up
        """
        view_layer = view_layer or bpy.context.scene.view_layers[0]
        assert isinstance(
            potential_root, (bpy.types.Collection, bpy.types.Object, str)
        ), f"root_object type ({type(potential_root)}) isn't allowed, must be Collection, Object, or str"
        if isinstance(potential_root, str):
            try:
                potential_root = bpy.data.collections[potential_root]
            except KeyError:
                try:
                    potential_root = bpy.data.objects[potential_root]
                except KeyError:
                    assert False, f"{potential_root} must be in bpy.data.collections"

        if force_visible:
            xp_file = self.createForestFileFromPotentialRoot(potential_root, view_layer)
        else:
            xp_file = forest_file.create_forest_single_file(potential_root)
        out = xp_file.write()

        if dest:
            with open(os.path.join(get_tmp_folder(), dest + ".for"), "w") as tmp_file:
                tmp_file.write(out)

        return out

    @staticmethod
    def get_XPlaneForExporter_log_content() -> List[str]:
        """
        Returns the content of the log file after export as a collection of lines, no trailing new lines,
        or KeyError if the text block doesn't exist yet (rare).
        """
        return [l.body for l in bpy.data.texts["XPlaneForExporter.log"].lines]


def get_source_folder() -> pathlib.Path:
    """Returns the full path to the addon folder"""
    return get_project_folder().joinpath("io_scene_xplane_for")


def get_project_folder() -> pathlib.Path:
    """Returns the full path to the project folder"""
    return os.path.dirname(pathlib.Path("..", __file__))


def get_tests_folder() -> pathlib.Path:
    return pathlib.Path(__file__).parent


def get_tmp_folder() -> pathlib.Path:
    return get_tests_folder().joinpath("tmp")


def make_fixture_path(dirname, filename, sub_dir="") -> pathlib.Path:
    return os.path.join(dirname, "fixtures", sub_dir, filename + ".for")


def runTestCases(testCases):
    # Until a better solution for knowing if the logger's error count should be used to quit the testing,
    # we are currently saying only 1 is allow per suite at a time (which is likely how it should be anyways)
    assert (
        len(testCases) == 1
    ), "Currently, only one test case per suite is supported at a time"
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(testCases[0])
    test_result = unittest.TextTestRunner().run(suite)

    # See XPlane2Blender/tests.py for documentation. The strings must be kept in sync!
    # This is not an optional debug print statement! The test runner needs this print statement to function
    print(
        f"RESULT: After {(test_result.testsRun)} tests got {len(test_result.errors)} errors, {len(test_result.failures)} failures, and {len(test_result.skipped)} skipped"
    )
