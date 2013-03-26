import os

from twisted.trial import unittest

from crawlmi.exceptions import NotConfigured
from crawlmi.tests import tests_dir
from crawlmi.utils.project import Project


sample_project_dir = os.path.join(tests_dir, 'sample_project')


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
            self.assertEqual(project.settings.get_int('TEST'), 42)

    def test_datadir(self):
        project = Project(path=sample_project_dir)
        self.assertEqual(project.data_dir, os.path.join(sample_project_dir, 'crawlmi_data'))
        self.assertTrue(os.path.exists(project.data_dir))
        os.rmdir(project.data_dir)

    def test_bad_project(self):
        project = Project(path=os.path.dirname(__file__))
        self.assertFalse(project.inside_project)
        self.assertIsNone(project.cfg_path)
        self.assertIsNone(project.cfg)
        self.assertIsNone(project.project_dir)
        self.assertDictEqual(project.settings.values, {})
        self.assertRaises(NotConfigured, project._get_data_dir)
