from unittest import TestCase, mock
from pathlib import Path

THIS_DIR = Path(__file__).parent
RESOURCES_DIR = THIS_DIR / "test_resources"


class TestComponentLibrary(TestCase):
    def test_standard_library_workflow(self):
        from tethys_components.library import Library as lib, ComponentLibrary

        mock_import = mock.patch("builtins.__import__").start()

        # TEST VALID ACCESSORS
        lib.tethys
        self.assertEqual(mock_import.call_args_list[-1][0][0], "tethys_components")
        self.assertEqual(mock_import.call_args_list[-1][0][3][0], "custom")
        lib.html
        self.assertEqual(mock_import.call_args_list[-1][0][0], "reactpy")
        self.assertEqual(mock_import.call_args_list[-1][0][3][0], "html")
        lib.hooks
        self.assertEqual(mock_import.call_args_list[-1][0][0], "tethys_components")
        self.assertEqual(mock_import.call_args_list[-1][0][3][0], "hooks")
        self.assertEqual(len(lib.styles), 0)
        self.assertIsNone(lib.parent_package)
        external_lib = lib.bs
        self.assertNotEqual(lib.bs, lib)
        self.assertIsInstance(external_lib, ComponentLibrary)
        self.assertIsNone(lib.bs.package)
        self.assertEqual(lib.bs.parent_package, "bs")
        self.assertEqual(len(lib.styles), 1)
        self.assertEqual(lib.styles[0], lib.STYLE_DEPS["bs"][0])
        self.assertDictEqual(lib.components_by_package, {})
        orig_func = ComponentLibrary.get_reactjs_module_wrapper_js
        mock_func = mock.MagicMock()
        ComponentLibrary.get_reactjs_module_wrapper_js = mock_func
        button_component = lib.bs.Button
        lib.bs.Button
        mock_func.assert_called_once()
        self.assertEqual(button_component, mock_import().web.export())
        mock.patch.stopall()

        # CREATE JAVASCRIPT WRAPPER FOR LIBRARY
        ComponentLibrary.get_reactjs_module_wrapper_js = orig_func
        content = lib.get_reactjs_module_wrapper_js()
        # (RESOURCES_DIR / 'expected_1.js').open('w+').write(content)  # Uncomment to write newly expected js
        self.assertEqual(content, (RESOURCES_DIR / "expected_1.js").open("r").read())

        # LOAD A NEW PAGE
        ComponentLibrary.refresh("new_page")
        self.assertDictEqual(lib.components_by_package, {})
        self.assertDictEqual(lib.package_handles, {})
        self.assertListEqual(lib.styles, [])
        self.assertListEqual(lib.defaults, [])
        self.assertEqual(lib.EXPORT_NAME, "new_page")

        # TRY TO ACCESS INVALID PACKAGE
        self.assertRaises(AttributeError, lambda: lib.does_not_exist)

        # REGISTER PACKAGE
        lib.register(
            "my-react-package@0.0.0",
            "does_not_exist",
            styles=["my_style.css"],
            use_default=True,
        )
        self.assertIn("does_not_exist", lib.PACKAGE_BY_ACCESSOR)
        self.assertEqual(
            lib.PACKAGE_BY_ACCESSOR["does_not_exist"], "my-react-package@0.0.0"
        )
        self.assertIn("does_not_exist", lib.STYLE_DEPS)
        self.assertListEqual(lib.STYLE_DEPS["does_not_exist"], ["my_style.css"])
        self.assertListEqual(lib.DEFAULTS, ["rp", "mapgl", "does_not_exist"])

        # REGISTER AGAIN EXACTLY
        lib.register(
            "my-react-package@0.0.0",
            "does_not_exist",
            styles=["my_style.css"],
            use_default=True,
        )

        # REGISTER NEW PACKAGE TO SAME ACCESSOR (NAUGHTY)
        self.assertRaises(
            ValueError, lib.register, "different-react-package@1.1.1", "does_not_exist"
        )

        # PREVIOUSLY INVALID PACKAGE NOW WORKS
        lib.does_not_exist  # Does not raise AttributeError it did before

        # LOAD COMPONENTS FROM SOURCE CODE
        mock_import = mock.patch("builtins.__import__").start()
        ComponentLibrary.get_reactjs_module_wrapper_js = mock_func
        test_source_code = """
        @compoenent
        def my_component():
            return lib.html.div(
                lib.pm.Map(),
                lib.bs.Button(Props(), "My Button"),
                lib.does_not_exist.Test()
            )
        """
        lib.load_dependencies_from_source_code(test_source_code)

        self.assertDictEqual(
            lib.components_by_package,
            {
                "pigeon-maps@0.21.6": ["Map"],
                "react-bootstrap@2.10.2": ["Button"],
                "my-react-package@0.0.0": ["Test"],
            },
        )
        self.assertIn("pm", lib.package_handles)
        self.assertIn("bs", lib.package_handles)
        self.assertIn("does_not_exist", lib.package_handles)
        self.assertIn("my_style.css", lib.styles)
        self.assertEqual(lib.defaults, ["Test"])
        ComponentLibrary.get_reactjs_module_wrapper_js = orig_func
        mock.patch.stopall()

        # EXPORT TO JS ONCE MORE
        content = lib.get_reactjs_module_wrapper_js()
        # (RESOURCES_DIR / 'expected_2.js').open('w+').write(content)  # Uncomment to write newly expected js
        self.assertEqual(content, (RESOURCES_DIR / "expected_2.js").open("r").read())
