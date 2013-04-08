import os

from twisted.trial import unittest

from crawlmi.core.project import Project
from crawlmi.exceptions import NotConfigured
from crawlmi.tests import tests_dir


sample_project_dir = os.path.join(tests_dir, 'test_project', 'sample_project')


class ProjectTest(unittest.TestCase):
    def test_good_project(self):
        project_dirs = [
            sample_project_dir,
            os.path.join(sample_project_dir, 'crawlmi_project'),
        ]

        for project_dir in project_dirs:
            project = Project(path=project_dir)
            self.assertTrue(project.inside_project)
            self.assertEqual(project.project_dir, sample_project_dir)
            self.assertEqual(project.module_settings.get_int('TEST'), 42)

    def test_data_dir(self):
        project = Project(path=sample_project_dir)
        self.assertEqual(project.data_dir, os.path.join(sample_project_dir, 'crawlmi_data'))
        self.assertTrue(os.path.exists(project.data_dir))
        os.rmdir(project.data_dir)

    def test_data_path(self):
        project = Project(path=sample_project_dir)
        # relative path
        expected = os.path.join(sample_project_dir, 'crawlmi_data', 'a', 'b')
        relative = project.data_path(os.path.join('a', 'b'), create_dir=False)
        self.assertEqual(relative, expected)
        self.assertFalse(os.path.exists(expected))
        # create dir
        project.data_path(os.path.join('a', 'b'), create_dir=True)
        self.assertTrue(os.path.exists(expected))
        os.rmdir(os.path.join(sample_project_dir, 'crawlmi_data', 'a', 'b'))
        os.rmdir(os.path.join(sample_project_dir, 'crawlmi_data', 'a'))
        # absolute path
        expected = os.path.abspath(__file__)
        absolute = project.data_path(expected, create_dir=False)
        self.assertEqual(absolute, expected)

        os.rmdir(project.data_dir)

    def test_bad_project(self):
        project = Project(path=os.path.dirname(__file__))
        self.assertFalse(project.inside_project)
        self.assertIsNone(project.cfg_path)
        self.assertIsNone(project.cfg)
        self.assertIsNone(project.project_dir)
        self.assertDictEqual(project.module_settings.values, {})
        self.assertRaises(NotConfigured, project._get_data_dir)

    def test_dummy_project(self):
        project = Project(path=None)
        self.assertFalse(project.inside_project)
        self.assertIsNone(project.cfg_path)
        self.assertIsNone(project.cfg)
        self.assertIsNone(project.project_dir)
        self.assertDictEqual(project.module_settings.values, {})
        self.assertRaises(NotConfigured, project._get_data_dir)
